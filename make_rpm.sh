#!/bin/bash
source VERSION

fpm -s dir -t rpm -n ${NAME} --version ${VERSION} -p ${NAME}-${VERSION}.rpm \
      gsiam.py=/usr/lib/yum-plugins/gsiam.py \
      gsiam.conf=/etc/yum/pluginconf.d/gsiam.conf
