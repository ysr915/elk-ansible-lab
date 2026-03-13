# ELK Stack Deployment with Ansible + AI Synthesis

Automated deployment of a full ELK (Elasticsearch, Logstash, Kibana) stack across 3 virtual machines using Ansible, with real-time log collection via Filebeat and an AI-powered data synthesis dashboard powered by Groq.

---

## Architecture
```
Windows Host (WSL2 - Ansible Control Node)
├── VM1: Elasticsearch  (192.168.56.11:9200)
├── VM2: Logstash       (192.168.56.12:5044)
└── VM3: Kibana         (192.168.56.13:5601)
                         AI Synthesis App (192.168.56.13:5000)
```

### Data Flow
```
All 3 VMs (syslog + auth.log)
    ↓ Filebeat
Logstash (192.168.56.12:5044)
    ↓
Elasticsearch (192.168.56.11:9200)
    ↓
Kibana Dashboard (192.168.56.13:5601)
    ↓
AI Synthesis App (192.168.56.13:5000)
    ↓
Groq API (Llama 3) → Natural Language Summary
```

---

## Prerequisites

Make sure you have the following installed on your Windows machine:

- [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
- [Vagrant](https://developer.hashicorp.com/vagrant/downloads)
- [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu
- A free [Groq API key](https://console.groq.com)

---

## Project Structure
```
elk-ansible-lab/
├── Vagrantfile                          # VM definitions
├── inventory.ini                        # Ansible inventory
├── site.yml                             # Master playbook
├── filebeat.yml                         # Filebeat playbook
├── ai_synthesis.yml                     # AI app playbook
└── roles/
    ├── elasticsearch/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── templates/elasticsearch.yml.j2
    │   └── vars/main.yml
    ├── logstash/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── templates/logstash.conf.j2
    │   └── vars/main.yml
    ├── kibana/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── templates/kibana.yml.j2
    │   └── vars/main.yml
    ├── filebeat/
    │   ├── tasks/main.yml
    │   ├── handlers/main.yml
    │   ├── templates/filebeat.yml.j2
    │   └── vars/main.yml
    └── ai_synthesis/
        ├── tasks/main.yml
        ├── handlers/main.yml
        ├── templates/ai_synthesis.service.j2
        ├── files/app.py
        └── vars/main.yml
```

---

## Setup Guide

### Step 1 — Clone the repository
```bash
git clone https://github.com/ysr915/elk-ansible-lab.git
cd elk-ansible-lab
```

### Step 2 — Start the VMs

Open PowerShell and run:
```powershell
vagrant up
```

This will create and boot 3 Ubuntu VMs. This may take 5-10 minutes.

### Step 3 — Install Ansible in WSL

Open your WSL/Ubuntu terminal:
```bash
sudo apt update && sudo apt install ansible -y
```

### Step 4 — Generate SSH keys
```bash
ssh-keygen -t rsa -b 4096
```

Hit Enter 3 times to accept defaults.

### Step 5 — Add SSH key to each VM

SSH into each VM from PowerShell and add your public key:
```powershell
vagrant ssh elasticsearch
```

Inside the VM:
```bash
echo "YOUR_PUBLIC_KEY" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
exit
```

Repeat for `logstash` and `kibana`. Get your public key with:
```bash
cat ~/.ssh/id_rsa.pub
```

### Step 6 — Test Ansible connectivity
```bash
cd ~/elk-ansible-lab
ansible -i inventory.ini all -m ping
```

All 3 VMs should return `pong`.

### Step 7 — Deploy ELK Stack
```bash
ansible-playbook -i inventory.ini site.yml
```

### Step 8 — Deploy Filebeat
```bash
ansible-playbook -i inventory.ini filebeat.yml
```

### Step 9 — Add your Groq API key

Edit the vars file:
```bash
nano roles/ai_synthesis/vars/main.yml
```

Replace `YOUR_GROQ_API_KEY_HERE` with your actual key from [console.groq.com](https://console.groq.com).

### Step 10 — Deploy AI Synthesis App
```bash
ansible-playbook -i inventory.ini ai_synthesis.yml
```

---

## Access the Services

| Service | URL |
|---|---|
| Kibana Dashboard | http://192.168.56.13:5601 |
| Elasticsearch API | http://192.168.56.11:9200 |
| AI Synthesis App | http://192.168.56.13:5000 |

---

## What Gets Deployed

### ELK Stack
- **Elasticsearch** — stores and indexes all data, configured in single-node mode with security disabled for lab use
- **Logstash** — receives logs from Filebeat on port 5044, routes airport data to dedicated index and system logs to filebeat index
- **Kibana** — visualizes data with dashboards and maps

### Filebeat
Installed on all 3 VMs, collects:
- `/var/log/syslog` — system logs
- `/var/log/auth.log` — authentication logs
- `/home/vagrant/airports_geo.ndjson` — airports dataset (on elasticsearch VM only)

### AI Synthesis App
A Flask web app that:
1. Queries Elasticsearch for live stats (log counts, airports data)
2. Sends data to Groq's Llama 3 model
3. Displays an AI-generated natural language summary of the data

---

## Suspending and Resuming

To suspend all VMs:
```powershell
vagrant suspend
```

To resume:
```powershell
vagrant resume
```

---

## Troubleshooting

**VMs unreachable after resume:**
```bash
vagrant reload
```

**Clock sync issues after suspend:**
```bash
ansible -i inventory.ini all -m shell -a "sudo timedatectl set-ntp true && sudo systemctl restart systemd-timesyncd" -u vagrant
```

**Elasticsearch not starting:**
```bash
vagrant ssh elasticsearch
sudo journalctl -xeu elasticsearch.service | tail -30
```

**AI Synthesis showing unavailable:**
- Check your Groq API key is correctly set in the service file
- Verify the model name is `llama-3.3-70b-versatile`

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Vagrant | VM provisioning |
| VirtualBox | Hypervisor |
| WSL2 | Ansible control node on Windows |
| Ansible | Configuration management |
| Elasticsearch | Data storage and search |
| Logstash | Data processing pipeline |
| Kibana | Data visualization |
| Filebeat | Log shipping |
| Python/Flask | AI synthesis web app |
| Groq API | LLM inference (Llama 3) |
| Git/GitHub | Version control |
