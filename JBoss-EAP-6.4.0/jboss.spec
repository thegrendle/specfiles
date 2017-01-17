%define jboss_version_full 	6.4.0
%define jboss_version_major 	6.4
%define jboss_fullname 		jboss-eap-%{jboss_version_full}
%define jboss_installdir	/opt
%define jboss_user 		jboss-as
%define jboss_user_uid 		600
%define jboss_group 		jboss-as
%define jboss_group_gid		600
%define jboss_service 		jboss-as
%define jboss_logdir 		/var/log/jboss-as
%define runuser                 %{jboss_user}
%define                         __jar_repack %{nil}


Summary:			JBoss Application Server
Name:           		jboss-eap
Version:        		%{jboss_version_full}
Release:        		2
License:        		LGPL
BuildArch:      		x86_64
Group:          		Applications/System
Source0:        		jboss-eap-%{jboss_version_full}.zip
Patch0:				jboss-eap-6.4.0-2.DB.patch
Requires:       		shadow-utils
Requires:       		coreutils
Requires:       		java-1.8.0-openjdk
Requires:       		initscripts
Requires(post): 		/sbin/chkconfig
Requires(pre): 			/usr/sbin/useradd, /usr/bin/getent, /usr/sbin/groupadd
Requires(postun): 		/usr/sbin/userdel, /usr/sbin/groupdel
Requires(preun):		/sbin/service
BuildRoot:			%{_tmppath}/jboss-eap-%{version}-%{release}-root-%(%{__id_u} -n)


%description
The JBoss Application Server (Enterprise Edition)

%prep
%setup -n jboss-eap-%{jboss_version_major}

# Removes defunct Java options for Java 1.8.
#
%patch0 -p1

%install
cd %{_topdir}/BUILD

install -d -m 755 $RPM_BUILD_ROOT/etc/profile.d
install -d -m 755 $RPM_BUILD_ROOT/etc/conf.d
install -d -m 755 $RPM_BUILD_ROOT%{jboss_installdir}/%{jboss_fullname}
install -d -m 755 $RPM_BUILD_ROOT%{jboss_installdir}/%{jboss_fullname}/server/default/conf
install -d -m 755 $RPM_BUILD_ROOT/var/run/%{jboss_service}
cp -R jboss-eap-%{jboss_version_major}/* $RPM_BUILD_ROOT%{jboss_installdir}/%{jboss_fullname}

# it caused adding bad requires for package
/bin/rm -rf $RPM_BUILD_ROOT%{jboss_installdir}/%{jboss_fullname}/bin/jboss_init_solaris.sh 2>&1

# Remove standalone xml file
# /bin/rm -rf $RPM_BUILD_ROOT%{jboss_installdir}/%{jboss_fullname}/standalone/configuration/standalone.xml 2>&1

install -d -m 755 $RPM_BUILD_ROOT%{_initrddir}
install -d -m 755 $RPM_BUILD_ROOT/etc/sysconfig
install -d -m 755 $RPM_BUILD_ROOT/etc/sysconfig/%{jboss_fullname}
install -d -m 755 $RPM_BUILD_ROOT/etc/jboss-as

#cp -R jboss-eap-%{jboss_version_major}/bin/init.d/jboss-as-standalone.sh $RPM_BUILD_ROOT%{_initrddir}/jboss
#cp -R jboss-eap-%{jboss_version_major}/bin/init.d/jboss-as.conf $RPM_BUILD_ROOT/etc/jboss-as/jboss-as.conf

# If jboss is running, kill it
# maxcount in seconds to wait before hitting
# with the big hammer
MAXCOUNT=30
INCREMENT=3

# assert modulus of MAXCOUNT by INCREMENT is 0
if [ ! $(($MAXCOUNT % $INCREMENT)) -eq 0 ];then
	echo "the modulus of MAXCOUNT ($MAXCOUNT) and INCREMENT ($INCREMENT) is nonzero"
	exit 1;
fi

PID=`ps -e -o pid,args|grep -v grep|grep java|grep run.sh|awk '{print $1}'`

if [ -n "$PID" ];then
	kill -15 $PID
fi

PID=`ps -e -o pid,args|grep -v grep|grep java|grep run.sh|awk '{print $1}'`

if [ -n "$PID" ];then
	for x in `seq $MAXCOUNT -$INCREMENT 0`;do
	PID=`ps -e -o pid,args|grep -v grep|grep java|grep run.sh|awk '{print $1}'`
	kill -15 $PID
	PID=`ps -e -o pid,args|grep -v grep|grep java|grep run.sh|awk '{print $1}'`
if [ -z "$PID" ];then
	break
fi
	sleep $INCREMENT
	done
fi
# make sure we succeeded
PID=`ps -e -o pid,args|grep -v grep|grep java|grep run.sh|awk '{print $1}'`
if [ -n "$PID" ];then
	kill -9 $PID
fi

# Does %{jboss_logdir} exist? if not, create it and set ownership to jboss
if [ ! -d $RPM_BUILD_ROOT/%{jboss_logdir} ];then
	mkdir -p $RPM_BUILD_ROOT/%{jboss_logdir}
        chmod -R 750 $RPM_BUILD_ROOT/%{jboss_logdir}
fi

cat > "$RPM_BUILD_ROOT%{_initrddir}/%{jboss_service}" << "EOF"
#!/bin/sh
#
# JBoss standalone control script
#
# chkconfig: - 80 20
# description: JBoss AS Standalone
# processname: standalone
# pidfile: /var/run/%{jboss_service}/jboss-standalone.pid
# config: /etc/jboss-as/jboss-as.conf

# Source function library.
. /etc/init.d/functions

# Load Java configuration.
[ -r /etc/java/java.conf ] && . /etc/java/java.conf
export JAVA_HOME

# Load JBoss AS init.d configuration.
if [ -z "$JBOSS_CONF" ]; then
  JBOSS_CONF="/etc/jboss-as/jboss-as.conf"
fi

[ -r "$JBOSS_CONF" ] && . "${JBOSS_CONF}"

# Set defaults.

if [ -z "$JBOSS_HOME" ]; then
  JBOSS_HOME=%{jboss_installdir}/%{jboss_fullname}
fi
export JBOSS_HOME

if [ -z "$JBOSS_PIDFILE" ]; then
  JBOSS_PIDFILE=/var/run/%{jboss_service}/jboss-standalone.pid
fi
export JBOSS_PIDFILE

if [ -z "$JBOSS_CONSOLE_LOG" ]; then
  JBOSS_CONSOLE_LOG=%{jboss_logdir}/console.log
fi

if [ -z "$STARTUP_WAIT" ]; then
  STARTUP_WAIT=120
fi

if [ -z "$SHUTDOWN_WAIT" ]; then
  SHUTDOWN_WAIT=120
fi

if [ -z "$JBOSS_CONFIG" ]; then
  JBOSS_CONFIG=standalone.xml
fi

JBOSS_SCRIPT=$JBOSS_HOME/bin/standalone.sh

prog='jboss-as'

CMD_PREFIX=''

if [ ! -z "$JBOSS_USER" ]; then
  if [ -x /etc/rc.d/init.d/functions ]; then
    CMD_PREFIX="daemon --user $JBOSS_USER"
  else
    CMD_PREFIX="su - $JBOSS_USER -c"
  fi
fi

start() {
  echo -n "Starting $prog: "
  if [ -f $JBOSS_PIDFILE ]; then
    read ppid < $JBOSS_PIDFILE
    if [ `ps --pid $ppid 2> /dev/null | grep -c $ppid 2> /dev/null` -eq '1' ]; then
      echo -n "$prog is already running"
      failure
      echo
      return 1 
    else
      rm -f $JBOSS_PIDFILE
    fi
  fi
  mkdir -p $(dirname $JBOSS_CONSOLE_LOG)
  cat /dev/null > $JBOSS_CONSOLE_LOG

  mkdir -p $(dirname $JBOSS_PIDFILE)
  chown $JBOSS_USER $(dirname $JBOSS_PIDFILE) || true
  #$CMD_PREFIX JBOSS_PIDFILE=$JBOSS_PIDFILE $JBOSS_SCRIPT 2>&1 > $JBOSS_CONSOLE_LOG &
  #$CMD_PREFIX JBOSS_PIDFILE=$JBOSS_PIDFILE $JBOSS_SCRIPT &

  if [ ! -z "$JBOSS_USER" ]; then
    if [ -x /etc/rc.d/init.d/functions ]; then
      daemon --user $JBOSS_USER LAUNCH_JBOSS_IN_BACKGROUND=1 JBOSS_PIDFILE=$JBOSS_PIDFILE $JBOSS_SCRIPT -c $JBOSS_CONFIG 2>&1 > $JBOSS_CONSOLE_LOG &
    else
      su - $JBOSS_USER -c "LAUNCH_JBOSS_IN_BACKGROUND=1 JBOSS_PIDFILE=$JBOSS_PIDFILE $JBOSS_SCRIPT -c $JBOSS_CONFIG" 2>&1 > $JBOSS_CONSOLE_LOG &
    fi
  fi

  count=0
  launched=false

  until [ $count -gt $STARTUP_WAIT ]
  do
    grep 'JBoss AS.*started in' $JBOSS_CONSOLE_LOG > /dev/null 
    if [ $? -eq 0 ] ; then
      launched=true
      break
    fi 
    sleep 1
    let count=$count+1;
  done
  
  success
  echo
  return 0
}

stop() {
  echo -n $"Stopping $prog: "
  count=0;

  if [ -f $JBOSS_PIDFILE ]; then
    read kpid < $JBOSS_PIDFILE
    let kwait=$SHUTDOWN_WAIT

    # Try issuing SIGTERM

    kill -15 $kpid
    until [ `ps --pid $kpid 2> /dev/null | grep -c $kpid 2> /dev/null` -eq '0' ] || [ $count -gt $kwait ]
    do
      sleep 1
      let count=$count+1;
    done

    if [ $count -gt $kwait ]; then
      kill -9 $kpid
    fi
  fi
  rm -f $JBOSS_PIDFILE
  success
  echo
}

status() {
  if [ -f $JBOSS_PIDFILE ]; then
    read ppid < $JBOSS_PIDFILE
    if [ `ps --pid $ppid 2> /dev/null | grep -c $ppid 2> /dev/null` -eq '1' ]; then
      echo "$prog is running (pid $ppid)"
      return 0
    else
      echo "$prog dead but pid file exists"
      return 1
    fi
  fi
  echo "$prog is not running"
  return 3
}

case "$1" in
  start)
      start
      ;;
  stop)
      stop
      ;;
  restart)
      $0 stop
      $0 start
      ;;
  status)
      status
      ;;
  *)
      ## If no parameters are given, print which are avaiable.
      echo "Usage: $0 {start|stop|status|restart|reload}"
      exit 1
      ;;
esac
EOF

cat > "$RPM_BUILD_ROOT/etc/jboss-as/jboss-as.conf" << "EOF"
# General configuration for the init.d scripts,
# not necessarily for JBoss AS itself.

# The username who should own the process.
#
JBOSS_USER=%{jboss_user}

# The amount of time to wait for startup
#
STARTUP_WAIT=120

# The amount of time to wait for shutdown
#
SHUTDOWN_WAIT=120

# Location to keep the console log
#
JBOSS_CONSOLE_LOG=%{jboss_logdir}/console.log
EOF


# Reload the profile
for i in /etc/profile.d/*.sh ; do
        if [ -x $i ]; then
                . $i
        fi
done


source /etc/profile

%clean
/bin/rm -Rf $RPM_BUILD_ROOT


%pre

if [ $1 -eq 1 ];
then
  { /usr/bin/getent passwd %{jboss_user}; } &> /dev/null && { userdel %{jboss_user}; } &> /dev/null
  { /usr/bin/getent group %{jboss_group}; } &> /dev/null && { groupdel %{jboss_group}; } &> /dev/null
  { /usr/bin/getent group %{jboss_group}; } &> /dev/null || groupadd -g %{jboss_group_gid} %{jboss_group} >/dev/null
  { /usr/bin/getent passwd %{jboss_user}; } &> /dev/null || useradd -r %{jboss_user} -u %{jboss_user_uid} -d %{jboss_installdir}/%{jboss_fullname} -g %{jboss_group_gid} -s /bin/bash >/dev/null 2>&1
#elif [ $1 -eq 2 ];
#then
fi

%post

if [ $1 -eq 1 ];
then
  /sbin/chkconfig --add %{jboss_service}
  [ -h %{jboss_installdir}/jboss ] && /sbin/rm -Rf %{jboss_installdir}/jboss
  [ -d %{jboss_installdir}/%{jboss_fullname} ] && /bin/ln -s %{jboss_installdir}/%{jboss_fullname} %{jboss_installdir}/jboss
fi

%postun

if [ $1 -eq 0 ];
then

  { /usr/bin/getent passwd %{jboss_user}; } &> /dev/null && { userdel %{jboss_user}; } &> /dev/null
  { /usr/bin/getent group %{jboss_group}; } &> /dev/null && { groupdel %{jboss_group}; } &> /dev/null

  #  We don't delete logs just because we uninstall a package.  Boo!
  #
  #if [ -d %{jboss_logdir} ]; then
  #/bin/rm -fr %{jboss_logdir} >/dev/null 2>&1
  #fi

  #  Delete the JBoss Home directory if it still exists
  #
  [ -d %{jboss_installdir}/%{jboss_fullname} ] && /bin/rm -fr %{jboss_installdir}/%{jboss_fullname} >/dev/null 2>&1

  #  Delete the Symbolic Link to the JBoss directory
  #
  [ -h %{jboss_installdir}/jboss ] && /bin/rm -Rf %{jboss_installdir}/jboss;

#elif [ $1 -eq 1 ];
#then
fi

%preun

/sbin/service %{jboss_service} status && service %{jboss_service} stop &> /dev/null


%files
%defattr(-,%{jboss_user},%{jboss_group})
%dir %{jboss_installdir}/%{jboss_fullname}
%dir %{jboss_logdir}
%dir /var/run/%{jboss_service}
%dir /etc/jboss-as
%config(noreplace) /etc/jboss-as/jboss-as.conf
%attr(755,root,root) /etc/rc.d/init.d/%{jboss_service}
%{jboss_installdir}/%{jboss_fullname}/*

%changelog
* Tue Jan 17 2017 Darryl Blonski <darryl.blonski@cyone.com> 6.4.0-2
- Created and added patch to remove defunct Java options.

* Tue Jan 17 2017 Darryl Blonski <darryl.blonski@cyone.com> 6.4.0-1
- Initial creation of JBoss EAP 6.4.0 RPM. 
