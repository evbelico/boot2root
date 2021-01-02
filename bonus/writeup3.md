# Combining certain directives, together with special keys, affecting the way Syslinux behaves, specially during the initial boot time.

## Basic case
Using the following basic configuration, Syslinux will automatically launch live:

We can find the default configuration in ```isolinux.cfg``` which is globally defined like:
```sh
 DEFAULT live
 prompt 0
 
 LABEL live
 KERNEL /casper/vmlinuz
 ```

## Escape keys
To avoid the automatic launch of the DEFAULT command, press any one of the [Shift] or [Alt] keys, or set [Caps Lock] or [Scroll lock], during boot time.

### Menu shiftkey
If you press shift when the virtual machine is booting, it will display a user-friendly boot menu with several choices - instead of automatically booting the DEFAULT label -.

We then find ourselves in a prompt where we can change the value of init:
```sh
boot: live init=/bin/sh
/bin/sh: 0: can not access tty; job control turned off
# whoami
root
#
```

Well done you are root !!
