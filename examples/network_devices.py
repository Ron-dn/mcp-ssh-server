#!/usr/bin/env python3
"""
Network Device Automation Example for MCP SSH Server.

This example demonstrates how to use the MCP SSH server for network device
management, including Cisco switches, routers, and other network equipment.
Based on the user's original check_status.exp script.
"""

import json
import time


def network_device_examples():
    """Examples for network device automation."""
    
    print("=== Network Device Automation Examples ===")
    print("Based on your original check_status.exp script\n")
    
    # Example 1: Connect to AUTO-01 switch
    print("1. Connect to AUTO-01 Switch:")
    auto01_connect = {
        "name": "mcp_ssh_connect",
        "arguments": {
            "host": "WDY1947100025",
            "username": "dnroot",
            "password": "dnroot",
            "port": 22,
            "timeout": 30
        }
    }
    print(json.dumps(auto01_connect, indent=2))
    
    # Simulated connection response
    auto01_connection_id = "ssh_abc123_WDY1947100025_dnroot"
    print(f"✓ Connected: {auto01_connection_id}\n")
    
    # Example 2: Check interface status on AUTO-01
    print("2. Check Interface Status on AUTO-01:")
    interface_commands = [
        "show interface ge100-0/0/12 | include 'Admin\\|Physical\\|Operational'",
        "show interface ge100-0/0/14 | include 'Admin\\|Physical\\|Operational'",
        "show interface ge100-0/0/17 | include 'Admin\\|Physical\\|Operational'",
        "show interface ge100-0/0/18 | include 'Admin\\|Physical\\|Operational'"
    ]
    
    check_interfaces = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": auto01_connection_id,
            "commands": interface_commands,
            "stop_on_error": False
        }
    }
    print(json.dumps(check_interfaces, indent=2))
    print("✓ Interface status checked\n")
    
    # Example 3: Connect to DN01 switch
    print("3. Connect to DN01 Switch:")
    dn01_connect = {
        "name": "mcp_ssh_connect",
        "arguments": {
            "host": "WDY19B7H00024-P3",
            "username": "dnroot",
            "password": "dnroot",
            "port": 22,
            "timeout": 30
        }
    }
    print(json.dumps(dn01_connect, indent=2))
    
    dn01_connection_id = "ssh_def456_WDY19B7H00024-P3_dnroot"
    print(f"✓ Connected: {dn01_connection_id}\n")
    
    # Example 4: Check DN01 interfaces
    print("4. Check DN01 Interface Status:")
    dn01_interfaces = [
        "show interface ge100-0/0/2 | include 'Admin\\|Physical\\|Operational'",
        "show interface ge100-0/0/3 | include 'Admin\\|Physical\\|Operational'",
        "show interface ge100-0/0/4 | include 'Admin\\|Physical\\|Operational'",
        "show interface ge100-0/0/5 | include 'Admin\\|Physical\\|Operational'"
    ]
    
    check_dn01_interfaces = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": dn01_connection_id,
            "commands": dn01_interfaces,
            "stop_on_error": False
        }
    }
    print(json.dumps(check_dn01_interfaces, indent=2))
    print("✓ DN01 interface status checked\n")
    
    # Example 5: Connect to Leaf Switch
    print("5. Connect to Leaf Switch:")
    leaf_connect = {
        "name": "mcp_ssh_connect",
        "arguments": {
            "host": "lab-leaf01",
            "username": "dn",
            "password": "drive1234!",
            "port": 22,
            "timeout": 30
        }
    }
    print(json.dumps(leaf_connect, indent=2))
    
    leaf_connection_id = "ssh_ghi789_lab-leaf01_dn"
    print(f"✓ Connected: {leaf_connection_id}\n")
    
    # Example 6: Check Leaf switch interfaces
    print("6. Check Leaf Switch Interface Status:")
    leaf_interfaces = [
        "show interfaces Ethernet8/33/1 status",
        "show interfaces Ethernet13/28/1 status",
        "show interfaces Ethernet8/35/1 status",
        "show interfaces Ethernet13/30/1 status",
        "show interfaces Ethernet8/34/1 status",
        "show interfaces Ethernet13/29/1 status",
        "show interfaces Ethernet8/36/1 status",
        "show interfaces Ethernet9/2/1 status"
    ]
    
    check_leaf_interfaces = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": leaf_connection_id,
            "commands": leaf_interfaces,
            "stop_on_error": False
        }
    }
    print(json.dumps(check_leaf_interfaces, indent=2))
    print("✓ Leaf switch interface status checked\n")
    
    # Example 7: Interactive command with enable mode
    print("7. Interactive Command (Enable Mode):")
    enable_command = {
        "name": "mcp_ssh_execute_interactive",
        "arguments": {
            "connection_id": auto01_connection_id,
            "command": "enable",
            "expect_prompts": ["Password:"],
            "responses": ["enable_password"],
            "timeout": 10
        }
    }
    print(json.dumps(enable_command, indent=2))
    print("✓ Entered enable mode\n")
    
    # Example 8: Configuration changes
    print("8. Configuration Changes:")
    config_commands = [
        "configure terminal",
        "interface ge100-0/0/12",
        "description Connected to Server-01",
        "no shutdown",
        "exit",
        "exit"
    ]
    
    configure_interface = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": auto01_connection_id,
            "commands": config_commands,
            "stop_on_error": True
        }
    }
    print(json.dumps(configure_interface, indent=2))
    print("✓ Interface configured\n")
    
    # Example 9: Save configuration
    print("9. Save Configuration:")
    save_config = {
        "name": "mcp_ssh_execute",
        "arguments": {
            "connection_id": auto01_connection_id,
            "command": "write memory",
            "timeout": 60
        }
    }
    print(json.dumps(save_config, indent=2))
    print("✓ Configuration saved\n")
    
    # Example 10: Bulk operations across all devices
    print("10. Bulk Operations - Get System Info from All Devices:")
    all_connections = [auto01_connection_id, dn01_connection_id, leaf_connection_id]
    
    for i, conn_id in enumerate(all_connections, 1):
        device_name = ["AUTO-01", "DN01", "Leaf-01"][i-1]
        print(f"  {device_name} System Info:")
        
        system_info = {
            "name": "mcp_ssh_get_system_info",
            "arguments": {
                "connection_id": conn_id
            }
        }
        print(f"    {json.dumps(system_info, indent=4)}")
    
    print("✓ System info retrieved from all devices\n")
    
    # Example 11: Disconnect all devices
    print("11. Disconnect All Devices:")
    for i, conn_id in enumerate(all_connections, 1):
        device_name = ["AUTO-01", "DN01", "Leaf-01"][i-1]
        
        disconnect = {
            "name": "mcp_ssh_disconnect",
            "arguments": {
                "connection_id": conn_id
            }
        }
        print(f"  Disconnect {device_name}: {json.dumps(disconnect)}")
    
    print("✓ All devices disconnected\n")


def advanced_network_examples():
    """Advanced network automation examples."""
    
    print("=== Advanced Network Automation ===\n")
    
    # Example 1: Backup configurations
    print("1. Backup Device Configurations:")
    backup_commands = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": "ssh_connection_id",
            "commands": [
                "show running-config",
                "show startup-config",
                "show version",
                "show inventory"
            ],
            "stop_on_error": False
        }
    }
    print(json.dumps(backup_commands, indent=2))
    print("✓ Configuration backup completed\n")
    
    # Example 2: Network discovery
    print("2. Network Discovery:")
    discovery_commands = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": "ssh_connection_id",
            "commands": [
                "show cdp neighbors detail",
                "show lldp neighbors detail",
                "show ip route",
                "show arp",
                "show mac address-table"
            ],
            "stop_on_error": False
        }
    }
    print(json.dumps(discovery_commands, indent=2))
    print("✓ Network discovery completed\n")
    
    # Example 3: Performance monitoring
    print("3. Performance Monitoring:")
    monitoring_commands = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": "ssh_connection_id",
            "commands": [
                "show processes cpu",
                "show memory",
                "show interfaces counters",
                "show environment all"
            ],
            "stop_on_error": False
        }
    }
    print(json.dumps(monitoring_commands, indent=2))
    print("✓ Performance monitoring completed\n")
    
    # Example 4: VLAN management
    print("4. VLAN Management:")
    vlan_commands = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": "ssh_connection_id",
            "commands": [
                "configure terminal",
                "vlan 100",
                "name Production",
                "exit",
                "interface ge100-0/0/12",
                "switchport mode access",
                "switchport access vlan 100",
                "exit",
                "exit"
            ],
            "stop_on_error": True
        }
    }
    print(json.dumps(vlan_commands, indent=2))
    print("✓ VLAN configuration completed\n")


def troubleshooting_examples():
    """Network troubleshooting examples."""
    
    print("=== Network Troubleshooting ===\n")
    
    # Example 1: Interface troubleshooting
    print("1. Interface Troubleshooting:")
    interface_troubleshoot = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": "ssh_connection_id",
            "commands": [
                "show interface ge100-0/0/12",
                "show interface ge100-0/0/12 counters",
                "show logging | include ge100-0/0/12",
                "show spanning-tree interface ge100-0/0/12"
            ],
            "stop_on_error": False
        }
    }
    print(json.dumps(interface_troubleshoot, indent=2))
    print("✓ Interface troubleshooting completed\n")
    
    # Example 2: Connectivity testing
    print("2. Connectivity Testing:")
    connectivity_test = {
        "name": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": "ssh_connection_id",
            "commands": [
                "ping 192.168.1.1 count 5",
                "traceroute 192.168.1.1",
                "show ip route 192.168.1.0",
                "show arp | include 192.168.1.1"
            ],
            "stop_on_error": False
        }
    }
    print(json.dumps(connectivity_test, indent=2))
    print("✓ Connectivity testing completed\n")


if __name__ == "__main__":
    print("MCP SSH Server - Network Device Automation Examples")
    print("=" * 60)
    
    # Show network device examples
    network_device_examples()
    
    print("=" * 60)
    advanced_network_examples()
    
    print("=" * 60)
    troubleshooting_examples()
    
    print("\nNote: These examples show the JSON requests that would be sent")
    print("to the MCP SSH server. In actual usage, these would be handled")
    print("automatically by your MCP client (like Claude Desktop).") 