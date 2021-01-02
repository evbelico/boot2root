# writeup2 - 

I checked the kernel version to see if any vulnerability exist

check kernel version : `uname –r` 

source check kernel version : https://phoenixnap.com/kb/check-linux-kernel-version

# looking for vulnerability and exploit on google.

There is a vulnerability called dirtycaw. This exploit change root user.
I found on a forum a github link with some dirtycow vulnerability exploit. I tried to use some of this exploit to change root user on boot2root iso. and one of them works. 

VulnerabilityDetails : 
A race condition was found in the way the Linux kernel's memory subsystem handled the copy-on-write (COW) breakage of private read-only memory mappings.
The bug has existed since around 2.6.22 (released in 2007) and was fixed on Oct 18, 2016.

Impact
An unprivileged local user could use this flaw to gain write access to otherwise read-only memory mappings and thus increase their privileges on the system.
This flaw allows an attacker with a local system account to modify on-disk binaries, bypassing the standard permission mechanisms that would prevent modification without an appropriate permission set.

source vulnerability : https://github.com/dirtycow/dirtycow.github.io/wiki/VulnerabilityDetails

source forum : https://github.com/FireFart/dirtycow/blob/master/dirty.c
source github exploit : https://github.com/dirtycow/dirtycow.github.io/wiki/PoCs
source github code exploit : https://github.com/FireFart/dirtycow/blob/master/dirty.c

# Usage --------------------

with this, we just have to compile it with : `gcc -pthread dirty.c -o dirty -lcrypt`
Then run the newly create binary by either doing: `"./dirty" or "./dirty my-new-password"`
and look at the user id. We are root : `id`
