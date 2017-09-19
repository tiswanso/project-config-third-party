#!/usr/bin/env python
#
# Generate devstack local.conf from jinja templates & yaml data.
# - Allow for multiple templates at global level and post-config file level
#
#

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

ASR_lconf_global_tmpl = """
disable_service q-l3
# Default routertype for Neutron routers                                                                                                                                      
Q_CISCO_DEFAULT_ROUTER_TYPE=ASR1k_router

enable_service ciscocfgagent
enable_service q-ciscorouter

"""

ASR_lconf_neutron_conf_tmpl = """
[DEFAULT]
api_extensions_path = extensions:/opt/stack/networking-cisco/networking_cisco/plugins/cisco/extensions

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

lconf_template_info = {
    "global": [ ASR_lconf_global_tmpl ],
    "postcfg_files": {
        "/etc/neutron/neutron.conf": [ ASR_lconf_neutron_conf_tmpl ]
    }
}

class NetCiscoLocalConf(object):
    def __init__(self, local_conf_info):
        self.local_conf_info = local_conf_info

    def _render_section(self, section_tmpl_list, template_data):
        section_data = ""
        for tmpl in section_tmpl_list:
            section_tmpl = jinja2.Template(tmpl)
            section_data += section_tmpl.render(template_data)
            section_data += "\n"
        return section_data

    def generate_local_conf(self, template_data_d):
        global_section = self._render_section(self.local_conf_info['global'], template_data_d)

        files_section = ""
        for postcfg_file in self.local_conf_info['postcfg_files']:
            files_section += "[[post-config|" + postcfg_file + "]]"
            files_section += self._render_section(self.local_conf_info['postcfg_files'][postcfg_file], template_data_d)

        return global_section + files_section

def main():
    """Output local.conf settings specific to networking-cisco plugins."""
    # TODO--add yaml file as param for testbed data; slurp in yaml file; render template from yaml
    topo_data = yaml.load(topo_data_yaml)
    asr_data = { 'topo_data': topo_data }
    lconf = NetCiscoLocalConf(lconf_template_info)
    asr_lconf = lconf.generate_local_conf(asr_data)
    print asr_lconf

if __name__ == '__main__':
    main()
