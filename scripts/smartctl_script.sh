#!/bin/bash
###скрипт создан Вишняковым Сергеем Дмитриевичем https://github.com/gera090, вопросы к нему :)
###script has created by Vishnyakov Sergey https://github.com/gera090, ask him :)
###get sorted sg list
sg_list=`ls -d /dev/* | awk '/^\/dev\/sg/' | sort -t 'g' -n -k2`
###loop through sg list
for one in $sg_list
do
    ###SMART access check
    if (`/usr/sbin/smartctl -a -d sat $one | grep "SMART support is: Enabled" > /dev/null`)
    then
          ###write the sg name as header in file
          echo $one >> /tmp/tmpf
          ###and write the result of smartctl below
          /usr/sbin/smartctl -A -d sat $one >> /tmp/tmpf
    fi
done
###print the content of the file onto the standard output stream
cat /tmp/tmpf
###remove temp file
rm -f /tmp/tmpf
