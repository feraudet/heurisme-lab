<?php
// Opens PHP sessions one after the other, like visitors arriving on a site,
// until session_start() fails. Session ids are fixed (md5 of the counter), so runs are identical.
for ($n = 0; ; $n++) {
    session_id(substr(md5((string) $n), 0, 26));
    if (!session_start()) {
        echo "session_start() failed after $n sessions\n";
        exit(1);
    }
    $_SESSION['uid'] = $n;
    session_write_close();
}
