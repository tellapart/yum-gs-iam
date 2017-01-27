FROM centos:7

RUN yum groupinstall -y 'Development Tools'
RUN yum install -y ruby-devel tar wget rpm which
RUN gem install fpm

COPY gsiam.py gsiam.conf VERSION make_rpm.sh /
