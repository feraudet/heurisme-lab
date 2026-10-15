/*
 * client.c : open-loop load generator for api.c.
 *
 * usage: client <ipv4> <requests> <interval_ms>
 * Request k is due at t0 + k * interval. Its latency is counted from that due time, not from the
 * moment it was actually sent, so a server that stalls cannot hide its stall from the measure.
 * 16 connections, request k goes on connection k % 16.
 * Prints one latency per line, in microseconds, in request order.
 */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

#define CONNS 16

static const char *host;
static int total, interval_ms;
static long long t0;
static long long *lat;

static long long now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static void *worker(void *arg) {
    int c = (int)(long)arg;
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one);
    struct sockaddr_in a = {.sin_family = AF_INET, .sin_port = htons(8080)};
    inet_pton(AF_INET, host, &a.sin_addr);
    if (connect(fd, (struct sockaddr *)&a, sizeof a)) {
        perror("connect");
        exit(1);
    }
    char buf[8];
    for (int k = c; k < total; k += CONNS) {
        long long due = t0 + (long long)k * interval_ms * 1000000LL;
        struct timespec ts = {due / 1000000000LL, due % 1000000000LL};
        clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL);
        if (write(fd, "q\n", 2) != 2) exit(1);
        int got = 0;
        while (got < 3) {
            ssize_t n = read(fd, buf + got, 3 - got);
            if (n <= 0) exit(1);
            got += n;
        }
        lat[k] = (now_ns() - due) / 1000;
    }
    close(fd);
    return NULL;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: client <ipv4> <requests> <interval_ms>\n");
        return 2;
    }
    host = argv[1];
    total = atoi(argv[2]);
    interval_ms = atoi(argv[3]);
    lat = calloc(total, sizeof *lat);
    t0 = now_ns() + 200000000LL; /* first request 200 ms after start, once all connections are open */
    pthread_t t[CONNS];
    for (int c = 0; c < CONNS; c++) pthread_create(&t[c], NULL, worker, (void *)(long)c);
    for (int c = 0; c < CONNS; c++) pthread_join(t[c], NULL);
    for (int k = 0; k < total; k++) printf("%lld\n", lat[k]);
    return 0;
}
