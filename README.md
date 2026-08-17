# Production Blog Platform — AWS

## Live Demo
 https://stayhealthylife.in/

## Overview
A fully functional multi-user blog platform
deployed on AWS with production-grade setup.
Handles real traffic with 99.9% uptime,
automated SSL renewal, and 24/7 monitoring.

## Features
- Multi-user authentication system
- Full CRUD — Create, Edit, Delete posts
- Comment system
- Secure HTTPS access
- 24/7 CloudWatch monitoring

## AWS Architecture

Internet
   ↓
GoDaddy Domain
   ↓
EC2 t3.small (Ubuntu)
├── Nginx (Web Server)
├── Gunicorn (WSGI)
└── Flask Application
         ↓
RDS PostgreSQL (Database)
         ↓
CloudWatch (Monitoring + Alerts)


## Technical Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python Flask |
| Database | PostgreSQL — AWS RDS |
| Server | AWS EC2 t3.small |
| Web Server | Nginx + Gunicorn |
| SSL | Let's Encrypt (Auto-renew) |
| Domain | GoDaddy |
| Monitoring | AWS CloudWatch |

## What Was Solved
❌ Before: App only ran on localhost
           No backup, no monitoring
           Not accessible 24/7

✅ After:  Production AWS deployment
           Automated SSL renewal
           Database on managed RDS
           24/7 uptime monitoring
           Real domain with HTTPS

## Screenshots
- Live website
  <img width="1685" height="897" alt="image" src="https://github.com/user-attachments/assets/2bf1f827-b6f5-4cf5-a567-193e300ae212" />
  <img width="1539" height="879" alt="image" src="https://github.com/user-attachments/assets/6de17dfe-87fc-4f05-b23b-3fcefdd28b31" />

- EC2 Console
- <img width="1723" height="822" alt="image" src="https://github.com/user-attachments/assets/1c488927-7ded-4f7a-81da-1ac9372874f4" />

- RDS Console
- <img width="1680" height="797" alt="image" src="https://github.com/user-attachments/assets/92fed3e3-45b4-4e98-8b74-672deb04dafd" />

- CloudWatch Dashboard
- <img width="1891" height="763" alt="image" src="https://github.com/user-attachments/assets/d7c8d76b-836d-4963-a9b7-8270a0d43204" />


## Key Metrics
- Response time: <100ms
- Concurrent users: 100+
- SSL: Auto-renews every 90 days
- Uptime: 99.9%
