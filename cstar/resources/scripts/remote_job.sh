#! /bin/sh

if test -f pid; then
    # We can't wait for things that aren't our children. Loop and sleep. :-(
    while ! test -f status; do
        sleep 10s
    done
    exit
fi

%s ./job >stdout 2>stderr &
echo $! >pid
wait $!
echo $? >status