#!/usr/bin/env python3
"""
Network Device Automation Examples

This module demonstrates how to use the MCP SSH server for network device management.
Based on common network automation scenarios and device management tasks.
"""

import json

def main():
    """
    Examples of network device automation using MCP SSH tools.
    These examples show how to manage switches, routers, and other network devices.
    """
    
    print("🌐 Network Device Management Examples\n")
    print("=" * 50)
    
    # Example 1: Connect to Core Switch
    print("1. Connect to Core Switch:")
    core_switch_connect = {
        "tool": "mcp_ssh_connect",
        "arguments": {
            "host": "core-switch-01.example.com",
            "port": 22,
            "username": "netadmin",
            "password": "your_password_here",
            "timeout": 30,
            "connection_id": "core_switch_session"
        }
    }
    print(json.dumps(core_switch_connect, indent=2))
    
    core_switch_connection_id = "ssh_abc123_core-switch-01_netadmin"
    print(f"✓ Connected: {core_switch_connection_id}\n")
    
    # Example 2: Check interface status on Core Switch
    print("2. Check Interface Status on Core Switch:")
    interface_commands = [
        "show interface GigabitEthernet1/0/1 | include 'Admin\\|Physical\\|Operational'",
        "show interface GigabitEthernet1/0/2 | include 'Admin\\|Physical\\|Operational'",
        "show interface GigabitEthernet1/0/3 | include 'Admin\\|Physical\\|Operational'",
        "show interface GigabitEthernet1/0/4 | include 'Admin\\|Physical\\|Operational'"
    ]
    
    check_interfaces = {
        "tool": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": core_switch_connection_id,
            "commands": interface_commands,
            "timeout": 10
        }
    }
    print(json.dumps(check_interfaces, indent=2))
    print("✓ Core switch interface status checked\n")
    
    # Example 3: Connect to Distribution Switch
    print("3. Connect to Distribution Switch:")
    dist_switch_connect = {
        "tool": "mcp_ssh_connect",
        "arguments": {
            "host": "dist-switch-01.example.com",
            "port": 22,
            "username": "netadmin",
            "password": "your_password_here",
            "timeout": 30,
            "connection_id": "dist_switch_session"
        }
    }
    print(json.dumps(dist_switch_connect, indent=2))
    
    dist_switch_connection_id = "ssh_def456_dist-switch-01_netadmin"
    print(f"✓ Connected: {dist_switch_connection_id}\n")
    
    # Example 4: Check Distribution Switch interfaces
    print("4. Check Distribution Switch Interface Status:")
    dist_interfaces = [
        "show interface GigabitEthernet2/0/1 | include 'Admin\\|Physical\\|Operational'",
        "show interface GigabitEthernet2/0/2 | include 'Admin\\|Physical\\|Operational'",
        "show interface GigabitEthernet2/0/3 | include 'Admin\\|Physical\\|Operational'",
        "show interface GigabitEthernet2/0/4 | include 'Admin\\|Physical\\|Operational'"
    ]
    
    check_dist_interfaces = {
        "tool": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": dist_switch_connection_id,
            "commands": dist_interfaces,
            "timeout": 10
        }
    }
    print(json.dumps(check_dist_interfaces, indent=2))
    print("✓ Distribution switch interface status checked\n")
    
    # Example 5: Connect to Access Switch
    print("5. Connect to Access Switch:")
    access_switch_connect = {
        "tool": "mcp_ssh_connect",
        "arguments": {
            "host": "access-switch-01.example.com",
            "port": 22,
            "username": "netadmin",
            "password": "your_password_here",
            "timeout": 30,
            "connection_id": "access_switch_session"
        }
    }
    print(json.dumps(access_switch_connect, indent=2))
    
    access_switch_connection_id = "ssh_ghi789_access-switch-01_netadmin"
    print(f"✓ Connected: {access_switch_connection_id}\n")
    
    # Example 6: Check Access Switch VLAN configuration
    print("6. Check Access Switch VLAN Configuration:")
    vlan_commands = [
        "show vlan brief",
        "show spanning-tree brief",
        "show interface status",
        "show mac address-table count"
    ]
    
    check_vlans = {
        "tool": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": access_switch_connection_id,
            "commands": vlan_commands,
            "timeout": 15
        }
    }
    print(json.dumps(check_vlans, indent=2))
    print("✓ Access switch VLAN configuration checked\n")
    
    # Example 7: Interactive troubleshooting session
    print("7. Interactive Network Troubleshooting:")
    troubleshoot_session = {
        "tool": "mcp_ssh_execute_interactive",
        "arguments": {
            "connection_id": core_switch_connection_id,
            "command": "ping 8.8.8.8",
            "expect_patterns": ["Success rate", "Timeout", "Unreachable"],
            "timeout": 30
        }
    }
    print(json.dumps(troubleshoot_session, indent=2))
    print("✓ Interactive troubleshooting session started\n")
    
    # Example 8: Backup device configurations
    print("8. Backup Device Configurations:")
    backup_commands = [
        "show running-config",
        "show startup-config",
        "show version",
        "show inventory"
    ]
    
    backup_config = {
        "tool": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": core_switch_connection_id,
            "commands": backup_commands,
            "timeout": 30
        }
    }
    print(json.dumps(backup_config, indent=2))
    print("✓ Configuration backup completed\n")
    
    # Example 9: Monitor device health
    print("9. Monitor Device Health:")
    health_commands = [
        "show processes cpu",
        "show memory statistics",
        "show environment temperature",
        "show environment power",
        "show logging | include ERROR"
    ]
    
    health_check = {
        "tool": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": core_switch_connection_id,
            "commands": health_commands,
            "timeout": 20
        }
    }
    print(json.dumps(health_check, indent=2))
    print("✓ Device health monitoring completed\n")
    
    # Example 10: Network connectivity tests
    print("10. Network Connectivity Tests:")
    connectivity_commands = [
        "ping 10.0.1.1 count 5",
        "traceroute 10.0.1.1",
        "show ip route 10.0.1.0",
        "show arp | include 10.0.1.1"
    ]
    
    connectivity_test = {
        "tool": "mcp_ssh_execute_multi",
        "arguments": {
            "connection_id": core_switch_connection_id,
            "commands": connectivity_commands,
            "timeout": 45
        }
    }
    print(json.dumps(connectivity_test, indent=2))
    print("✓ Network connectivity tests completed\n")
    
    # Example 11: Upload configuration files
    print("11. Upload Configuration Files:")
    upload_config = {
        "tool": "mcp_ssh_upload",
        "arguments": {
            "connection_id": core_switch_connection_id,
            "local_path": "/local/configs/switch-config.txt",
            "remote_path": "/tmp/new-config.txt",
            "recursive": False
        }
    }
    print(json.dumps(upload_config, indent=2))
    print("✓ Configuration file uploaded\n")
    
    # Example 12: Download logs and diagnostics
    print("12. Download Device Logs:")
    download_logs = {
        "tool": "mcp_ssh_download",
        "arguments": {
            "connection_id": core_switch_connection_id,
            "remote_path": "/var/log/system.log",
            "local_path": "/local/logs/core-switch-system.log",
            "recursive": False
        }
    }
    print(json.dumps(download_logs, indent=2))
    print("✓ Device logs downloaded\n")
    
    # Example 13: Batch operations across multiple devices
    print("13. Batch Operations Across Multiple Devices:")
    all_connections = [core_switch_connection_id, dist_switch_connection_id, access_switch_connection_id]
    
    for i, connection_id in enumerate(all_connections, 1):
        device_name = ["Core-Switch", "Dist-Switch", "Access-Switch"][i-1]
        
        system_info = {
            "tool": "mcp_ssh_get_system_info",
            "arguments": {
                "connection_id": connection_id
            }
        }
        print(f"  {device_name} System Info:")
        print(json.dumps(system_info, indent=4))
    
    print("✓ Batch system information gathered\n")
    
    # Example 14: Clean up all connections
    print("14. Clean Up All Connections:")
    for i, connection_id in enumerate(all_connections, 1):
        device_name = ["Core-Switch", "Dist-Switch", "Access-Switch"][i-1]
        
        disconnect = {
            "tool": "mcp_ssh_disconnect",
            "arguments": {
                "connection_id": connection_id
            }
        }
        print(f"  Disconnecting from {device_name}:")
        print(json.dumps(disconnect, indent=4))
    
    print("✓ All connections closed\n")
    
    print("=" * 50)
    print("🎯 Network Device Management Examples Complete!")
    print("\nThese examples demonstrate:")
    print("• Multi-device connectivity management")
    print("• Interface status monitoring")
    print("• Configuration backup and restore")
    print("• Health monitoring and diagnostics")
    print("• File transfer operations")
    print("• Batch operations across devices")
    print("• Interactive troubleshooting sessions")

if __name__ == "__main__":
    main() 