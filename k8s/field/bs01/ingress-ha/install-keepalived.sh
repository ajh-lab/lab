#!/bin/bash
set -euo pipefail
ip="$1"
case "$ip" in
  192.168.0.4) priority=150 ;;
  192.168.0.5) priority=140 ;;
  192.168.0.6) priority=130 ;;
  *) echo 'Unexpected node IP' >&2; exit 1 ;;
esac
ip -4 address show dev enp0s31f6 | grep -Fq "$ip/24"
test -f /etc/keepalived/bs01-console-ca.crt
test ! -f /etc/keepalived/keepalived.conf
cat > /usr/local/sbin/bs01-ingress-health <<EOF
#!/bin/sh
systemctl is-active --quiet k3s || exit 1
curl --silent --fail --max-time 2 --cacert /etc/keepalived/bs01-console-ca.crt --resolve console.bs01.droneops.home.arpa:443:$ip https://console.bs01.droneops.home.arpa/ -o /dev/null
EOF
chmod 0755 /usr/local/sbin/bs01-ingress-health
cat > /etc/keepalived/keepalived.conf <<EOF
global_defs {
  router_id BS01_${ip##*.}
  enable_script_security
  script_user root
}
vrrp_script ingress_ready {
  script "/usr/local/sbin/bs01-ingress-health"
  interval 2
  timeout 3
  fall 2
  rise 2
}
vrrp_instance BS01_INGRESS {
  state BACKUP
  interface enp0s31f6
  virtual_router_id 51
  priority $priority
  advert_int 1
  nopreempt
  unicast_src_ip $ip
  unicast_peer {
EOF
for peer in 192.168.0.4 192.168.0.5 192.168.0.6; do
  if [ "$peer" != "$ip" ]; then printf '    %s\n' "$peer" >> /etc/keepalived/keepalived.conf; fi
done
cat >> /etc/keepalived/keepalived.conf <<'EOF'
  }
  virtual_ipaddress {
    192.168.0.10/24 dev enp0s31f6
  }
  track_script {
    ingress_ready
  }
}
EOF
chmod 0600 /etc/keepalived/keepalived.conf
keepalived --config-test
/usr/local/sbin/bs01-ingress-health
systemctl enable --now keepalived
