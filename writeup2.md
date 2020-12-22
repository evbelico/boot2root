# writeup2 ------------------

First i looked for some informations about dirtycow vulnerability exploit. I found on a forum a github link with some dirtycow vulnerability exploit. I tried to use some of this exploit to change root user on boot2root iso. and one of them works. 
this is the code of the exploit : 

source forum : https://github.com/FireFart/dirtycow/blob/master/dirty.c
source github exploit : https://github.com/dirtycow/dirtycow.github.io/wiki/PoCs
source github code exploit : https://github.com/FireFart/dirtycow/blob/master/dirty.c

# Usage --------------------

with this, we just have to compile it with : `gcc -pthread dirty.c -o dirty -lcrypt`
Then run the newly create binary by either doing: `"./dirty" or "./dirty my-new-password"`
and look at the user id. We are root.
