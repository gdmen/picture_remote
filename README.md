sudo apt-get update
sudo apt-get dist-upgrade
sudo apt-get install fswebcam
sudo apt-get install imagemagick
// Turn on bluetooth remote
<pre>
You can try running bluetoothctl from the command line, make sure your device is on / ready to be discovered:

$ bluetoothctl
[NEW] Controller AA:BB:CC:DD:EE:FF device-name [default]
Any other bluetooth devices will be listed here. You'll then be inside a [bluetooth] prompt.

First, turn bluetooth power on (if your device is off):

[bluetooth]# power on
Changing power on succeeded
Then, make sure your agent is registered:

[bluetooth]# agent on
Agent registered

[bluetooth]# default-agent 
Default agent request successful
Now you can scan for devices from the console:

[bluetooth]# scan on
Discovery started
[CHG] Controller AA:BB:CC:DD:EE:FF Discovering: yes
[NEW] Device FF:EE:DD:CC:BB:AA Someone's Keyboard
You can manually pair from here as well:

[bluetooth]# pair FF:EE:DD:CC:BB:AA 
Attempting to pair with FF:EE:DD:CC:BB:AA 
[CHG] Device C8:E0:EB:04:52:55 Connected: yes
At this point, you should be prompted to enter a pin code for pairing:

Request PIN code
[agent] Enter PIN code: 12345
Enter a number (eg. 12345), and you will be prompted to input the same number from the device:

[Someone's Keyboard]# 12345
You should then be notified that your keyboard has paired:

[CHG] Device FF:EE:DD:CC:BB:AA Paired: yes
</pre>

Enable RPI ssh

scp picture_remote.py pi@<ip>:.
scp requirements.txt pi@<ip>:.

ssh into RPI:

pip install -r requirements.txt

sudo mv picture_remote.service /lib/systemd/system/

vi ~/.bashrc:
if [ $(tty) == /dev/tty1 ]; then
  python /home/pi/picture_remote.py > /tmp/picture_remote.log
fi
