#!/usr/bin/env python

import jinja2
import yaml


topo_data_yaml = """
routers:
  ASR_1:
    type: asr
    ipaddr: 10.0.198.207
    user: admin
    password: "CTO1234!"
    ports:
      intf:
        type: "data"
        intf: "te0/0/0"
  ASR_2:
    type: asr
    ipaddr: 10.0.198.206
    user: admin
    password: "CTO1234!"
    ports:
      intf:
        type: "data"
        intf: "te0/0/0"

"""

ASR_lconf_templ = """
disable_service q-l3
# Default routertype for Neutron routers                                                                                                                                      
Q_CISCO_DEFAULT_ROUTER_TYPE=ASR1k_router

enable_service ciscocfgagent
enable_service q-ciscorouter

[[post-config|/etc/neutron/neutron.conf]]

[hosting_devices_templates]
[cisco_hosting_device_template:1]
name=NetworkNode
enabled=True
host_category=Network_Node
service_types=router:FW:VPN
image=
flavor=
default_credentials_id=1
configuration_mechanism=
protocol_port=22
booting_time=360
slot_capacity=2000
desired_slots_free=0
tenant_bound=
device_driver=networking_cisco.plugins.cisco.device_manager.hosting_device_drivers.noop_hd_driver.NoopHostingDeviceDriver
plugging_driver=networking_cisco.plugins.cisco.device_manager.plugging_drivers.noop_plugging_driver.NoopPluggingDriver

[cisco_hosting_device_template:3]
name="ASR1k template"
enabled=True
host_category=Hardware
service_types=router:FW:VPN
image=
flavor=
default_credentials_id=1
configuration_mechanism=
protocol_port=22
booting_time=360
slot_capacity=2000
desired_slots_free=0
tenant_bound=
device_driver=networking_cisco.plugins.cisco.device_manager.hosting_device_drivers.noop_hd_driver.NoopHostingDeviceDriver
plugging_driver=networking_cisco.plugins.cisco.device_manager.plugging_drivers.hw_vlan_trunking_driver.HwVLANTrunkingPlugDriver

[router_types]

[cisco_router_type:1]
name=Namespace_Neutron_router
description="Neutron router implemented in Linux network namespace"
template_id=1
ha_enabled_by_default=False
shared=True
slot_need=0
scheduler=
driver=
cfg_agent_service_helper=
cfg_agent_driver=

[cisco_router_type:3]
name=ASR1k_router
description="Neutron router implemented in Cisco ASR1k device"
template_id=3
ha_enabled_by_default=True
shared=True
slot_need=2
scheduler=networking_cisco.plugins.cisco.l3.schedulers.l3_router_hosting_device_scheduler.L3RouterHostingDeviceHARandomScheduler
driver=networking_cisco.plugins.cisco.l3.drivers.asr1k.asr1k_routertype_driver.ASR1kL3RouterDriver
cfg_agent_service_helper=networking_cisco.plugins.cisco.cfg_agent.service_helpers.routing_svc_helper.RoutingServiceHelper
cfg_agent_driver=networking_cisco.plugins.cisco.cfg_agent.device_drivers.asr1k.asr1k_routing_driver.ASR1kRoutingDriver

[routing]
default_router_type = ASR1k_router

[hosting_device_credentials]
{% for router_name in topo_data.routers -%}
{% set router = topo_data.routers[router_name] -%}
{% if router.type == 'asr' -%}
[cisco_hosting_device_credential:{{ loop.index }}]
name="Universal credential"
description="Credential used for all hosting devices"
user_name = {{ router.user }}
password = {{ router.password }}
type=
{% endif -%}
{% endfor %}
[hosting_devices]

{% for router_name in topo_data.routers -%}
{% set router = topo_data.routers[router_name] -%}
{% if router.type == 'asr' -%}
[cisco_hosting_device:{{ loop.index }}]
template_id=3
credentials_id= {{ loop.index }}
device_id=SN:abcd1234efgh
admin_state_up=True
management_ip_address= {{ router.ipaddr }}
protocol_port=22
tenant_bound=
auto_delete=False

{% endif -%}
{% endfor -%}

[plugging_drivers]

{% for router_name in topo_data.routers -%}
{% set router = topo_data.routers[router_name] -%}
{% if router.type == 'asr' -%}
[HwVLANTrunkingPlugDriver:{{ loop.index }}]
{% for port_name in router.ports -%}
{% if router.ports[port_name].type == 'data' -%}
external_net_interface_1=*:{{ router.ports[port_name].intf }}
internal_net_interface_1=*:{{ router.ports[port_name].intf }}

{% endif -%}
{% endfor -%}
{% endif -%}
{% endfor -%}

"""

def main():
    """Output local.conf settings specific to networking-cisco plugins."""
    # TODO--add yaml file as param for testbed data; slurp in yaml file; render template from yaml
    topo_data = yaml.load(topo_data_yaml)
    asr_data = { 'topo_data': topo_data }
    asr_templ = jinja2.Template(ASR_lconf_templ)
    asr_lconf = asr_templ.render(asr_data)
    print asr_lconf

if __name__ == '__main__':
    main()
