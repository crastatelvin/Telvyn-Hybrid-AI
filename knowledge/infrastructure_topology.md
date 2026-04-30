# Aetherial Systems: Infrastructure Topology (2026)

## Cloud Regions
- **Primary:** AWS us-east-1 (Northern Virginia)
- **Secondary (DR):** AWS eu-central-1 (Frankfurt)

## Network Architecture
- **VPC ID:** vpc-0a1b2c3d4e5f
- **Subnets:**
    - Public: 10.0.1.0/24, 10.0.2.0/24
    - Private (App): 10.0.10.0/24, 10.0.11.0/24
    - Data (DB): 10.0.20.0/24, 10.0.21.0/24

## Load Balancer (ALB)
- **ID:** alb-prod-main
- **Health Check:** /health
- **Port:** 443 (SSL)
