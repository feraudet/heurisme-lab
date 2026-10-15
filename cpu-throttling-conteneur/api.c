/*
 * api.c : a tiny TCP API, used to show CFS throttling.
 *
 * - Each request ("q\n") costs 1 ms of CPU on the thread of its connection, then gets "ok\n".
 * - Every second, a background job (think: cache refresh, garbage collection) runs on 4 threads,
 *   50 ms of CPU each: 200 ms of CPU in one burst.
 *
 * CPU time is measured with CLOCK_THREAD_CPUTIME_ID, so the work is the same whatever the
 * machine does: what changes from one run to the next is only the wall time.
 *
 * For every job, prints one line on stdout: wall time of the job, and the pauses seen by
 * its threads (gaps of more than 2 ms of wall time between two 0.5 ms slices of CPU).
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#define PORT 8080
#define JOB_THREADS 4
#define JOB_CPU_MS 50
#define SLICE_US 500
#define SLICES (JOB_CPU_MS * 1000 / SLICE_US)
#define REQUEST_CPU_US 1000
#define PAUSE_MIN_NS 2000000LL

static long long now_ns(clockid_t clk) {
    struct timespec ts;
    clock_gettime(clk, &ts);
    return ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

/* Burn cpu_us microseconds of CPU time of the calling thread. */
static void burn(long long cpu_us) {
    long long end = now_ns(CLOCK_THREAD_CPUTIME_ID) + cpu_us * 1000LL;
    volatile unsigned long x = 0;
    while (now_ns(CLOCK_THREAD_CPUTIME_ID) < end) {
        for (int i = 0; i < 200; i++) x += i;
    }
}

/* ---------- requests ---------- */
static void *connection(void *arg) {
    int fd = (int)(long)arg;
    char buf[64];
    for (;;) {
        ssize_t n = read(fd, buf, sizeof buf);
        if (n <= 0) break;
        for (ssize_t i = 0; i < n; i++) {
            if (buf[i] == '\n') {
                burn(REQUEST_CPU_US);
                if (write(fd, "ok\n", 3) != 3) goto done;
            }
        }
    }
done:
    close(fd);
    return NULL;
}

static void *listener(void *arg) {
    (void)arg;
    int s = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &one, sizeof one);
    struct sockaddr_in a = {.sin_family = AF_INET, .sin_port = htons(PORT), .sin_addr.s_addr = INADDR_ANY};
    if (bind(s, (struct sockaddr *)&a, sizeof a) || listen(s, 64)) {
        perror("listen");
        exit(1);
    }
    for (;;) {
        int c = accept(s, NULL, NULL);
        if (c < 0) continue;
        setsockopt(c, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
        pthread_t t;
        pthread_create(&t, NULL, connection, (void *)(long)c);
        pthread_detach(t);
    }
    return NULL;
}

/* ---------- background job ---------- */
static pthread_barrier_t start_b, end_b;
static long long job_t0;
static long long marks[JOB_THREADS][SLICES]; /* wall time (ns since job start) at the end of each slice */

static void *job_thread(void *arg) {
    int k = (int)(long)arg;
    for (;;) {
        pthread_barrier_wait(&start_b);
        for (int s = 0; s < SLICES; s++) {
            burn(SLICE_US);
            marks[k][s] = now_ns(CLOCK_MONOTONIC) - job_t0;
        }
        pthread_barrier_wait(&end_b);
    }
    return NULL;
}

static int cmp_ll(const void *a, const void *b) {
    long long x = *(const long long *)a, y = *(const long long *)b;
    return (x > y) - (x < y);
}

int main(void) {
    setvbuf(stdout, NULL, _IOLBF, 0);
    pthread_t t;
    pthread_create(&t, NULL, listener, NULL);
    pthread_barrier_init(&start_b, NULL, JOB_THREADS + 1);
    pthread_barrier_init(&end_b, NULL, JOB_THREADS + 1);
    for (int k = 0; k < JOB_THREADS; k++) pthread_create(&t, NULL, job_thread, (void *)(long)k);

    static long long all[JOB_THREADS * SLICES];
    long long base = now_ns(CLOCK_MONOTONIC);
    for (int job = 1;; job++) {
        long long next = base + job * 1000000000LL;
        struct timespec ts = {next / 1000000000LL, next % 1000000000LL};
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL);
        job_t0 = now_ns(CLOCK_MONOTONIC);
        pthread_barrier_wait(&start_b);
        pthread_barrier_wait(&end_b);
        long long wall = now_ns(CLOCK_MONOTONIC) - job_t0;

        /* pauses: gaps in the merged slice marks, where no job thread made progress */
        int n = 0;
        for (int k = 0; k < JOB_THREADS; k++)
            for (int s = 0; s < SLICES; s++) all[n++] = marks[k][s];
        qsort(all, n, sizeof all[0], cmp_ll);
        printf("job %d wall_ms %.1f", job, wall / 1e6);
        long long prev = 0;
        for (int i = 0; i < n; i++) {
            if (all[i] - prev > PAUSE_MIN_NS)
                printf(" pause %.1f-%.1f", prev / 1e6, all[i] / 1e6);
            prev = all[i];
        }
        printf("\n");
    }
}
