# ESXi iLO Network Maintenance - 2026-10-21

Owning issue: [lab #68](https://github.com/ajh-lab/lab/issues/68).

## Current State

- ESXi host: `lab-vm-host`, observed hostname `OMAESXMGT01`, management
  `192.168.1.49`. Hardware is an HPE ProLiant DL360p Gen8, not a Windows
  workstation. ESXi remains `6.7.0 build-13006603`; no hypervisor upgrade occurred.
- iLO 4 firmware remains `2.77`. Verified MAC: `2C:59:E5:46:97:0E`.
- HPONCFG and IPMI readback confirm iLO moved from `192.168.0.39` to static
  `192.168.1.39/24`, gateway and primary DNS `192.168.1.1`, DHCP disabled.
  The dedicated port remains selected; shared-port and VLAN settings were not
  changed. UniFi has a verified reservation for this MAC/address because the
  address lies inside the existing DHCP pool.
- External iLO network acceptance passed after the owner connected the dedicated
  Ethernet cable: two ping replies, ARP resolving to the verified MAC, HTTPS 200
  with the iLO login page, and public device metadata identifying iLO 4 firmware
  2.77 on the DL360p Gen8. Authenticated iLO login was not tested; no iLO
  credentials were guessed or changed. HTTPS discovery used the existing
  self-signed device certificate without sending credentials; certificate trust
  has not been enrolled or verified against a trusted CA.
- All five formerly running VMs were restored. Four previously stopped VMs
  remain stopped. ESXi maintenance mode was exited.

## Authorization and Changes

The owner approved installing HPONCFG, selecting `192.168.1.39/24` if free,
gracefully stopping the guests, installing the required channel driver,
rebooting ESXi, restoring services, and completing the iLO address migration.
No account passwords, tokens, storage layout, RAID configuration, controller
firmware, guest packages, or DroneOps application versions were changed.

The target had no responding network neighbor or conflicting router client.
NetBox held an unnamed, unassigned `/32` inventory placeholder, not another
documented allocation; that record was reconciled to the configured iLO `/24`.

Installed only these HPE VIBs from the HTTPS HPE depot:

| Package | Installed Version | Reboot |
| --- | --- | --- |
| `hponcfg` | `6.7.0.5.4-0.3.7535516` | Not required |
| `ilo` | `670.10.2.0.2-1OEM.670.0.0.7535516` | Required and completed |

Both passed native ESXi dependency/acceptance dry runs. No signature bypass,
forced installation, or acceptance-level reduction was used. The utility is
`/opt/tools/hponcfg`; the loaded channel driver exposes `/dev/hpilo-*` devices.
Local configuration used only network-specific RIBCL commands, without password
changes or an iLO factory reset. ESXi management addressing was not changed.

## Shutdown and Recovery Evidence

The host's registered inventory contained nine VMs. All five running guests
reported working VMware Tools, and the Actions runner had no active job.
Graceful guest shutdown was requested in this order, and each powered-off state
was observed before continuing:

1. `lab-gha-runner-01`
2. `lab-prometheus01`
3. `lab-registry01`
4. `lab-pgsql01`
5. `lab-secrets01`

The driver was installed with all guests off. ESXi entered maintenance mode and
rebooted. New host uptime and successful pinned SSH access established the
reboot. The original autostart configuration was preserved; previously running
VMs were explicitly restored, and the complete nine-VM power-state inventory
matched the preflight snapshot.

| Guest / Service | Verified Recovery |
| --- | --- |
| `lab-pgsql01` | New boot identity, PostgreSQL 16 service running, `pg_isready` accepting connections |
| `lab-secrets01` | New boot identity, OpenBao active and unsealed with existing key, authenticated secret reads work |
| `lab-registry01` | New boot identity, Docker and registry container running, authenticated `/v2/` HTTP 200 |
| `lab-gha-runner-01` | New boot identity, all three runner units and release-catalog unit active; GitHub reports all three online |
| `lab-prometheus01` | VMware power cycle observed; readiness HTTP 200 and runtime API identifies `lab-prometheus01` with a fresh process start |
| CIM | `sfcbd is running` after the host reboot |
| Lab Kubernetes | All five nodes Ready; `openbao-store` returned Ready/Valid after unseal |
| DroneOps | Home-network HTTPS HTTP 200 with normal certificate validation |
| NetBox | Authenticated API returned successfully after the dependency outage |
| iLO LAN | Ping and matching ARP MAC; HTTPS login page HTTP 200 and expected hardware identity |

The four originally stopped VMs were `OMA01VMDC01`, `OMA01VMBK01`,
`OMA01WJMP01`, and `OMA01VCNTR01`; maintenance did not start them.

### Evidence Limits and Existing Conditions

- The pre-existing Prometheus SSH trust mismatch was not accepted or replaced.
  Prometheus recovery evidence is its API and VMware Tools, not an authenticated
  guest-shell inspection of every systemd unit.
- PostgreSQL's VM had a preflight `fwupd-refresh` failure. It was absent from the
  post-reboot failed-unit list. The four SSH-verified Linux guests had no failed
  units at recovery inspection. On-demand `fwupd`/`upower` processes did not need
  to be forced back to their earlier incidental running state.
- The lab External Secrets controller had a large historical restart count;
  its secret store recovered to Valid after unseal. No token-policy edits or
  credential rotation were performed as part of this maintenance.
- This does not complete RAID health reporting. Storage is an HPE Smart Array
  P420i using `nhpsa`; only generic VMware CIM providers were observed. No SMX
  provider or SSA CLI was installed, and online logical volumes are not proof
  of physical disk, RAID, or cache/battery health.

## Inventory and Remaining Acceptance

NetBox parent device `lab-vm-host` (device 8) retains its existing management
interface and primary ESXi address. Dedicated interface `iLO` (50) has primary
MAC record 7 and assigned IP record 43, `192.168.1.39/24`. Descriptions record
the verified network reachability and untested authenticated login. The stale
Windows-host description was corrected; no unrelated device records changed.

The network migration and authorized maintenance are complete. Future iLO
management or storage-health inspection must use separately verified iLO
credentials. No additional ESXi reboot, shared-NIC change, or VLAN change is
needed for this migration.

## References

- [HPE HPONCFG package](https://vibsdepot.hpe.com/sdx/downloads/sep2019/gen9v4/esxi-670-vibs/oncfg/)
- [HPE ESXi 6.7 iLO channel driver](https://vibsdepot.hpe.com/sdx/downloads/sep2019/gen9v4/esxi-670-vibs/ilo/)
- [HPE iLO 4 scripting guide](https://support.hpe.com/hpesc/public/api/document/c03334058)
- [VMware CIM enablement](https://knowledge.broadcom.com/external/article/313877/how-to-disable-or-enable-the-sfcb-servic.html)
