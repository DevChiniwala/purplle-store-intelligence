# Deployment Guide: Purplle Store Intelligence

This guide walks you through deploying the complete backend system (API, Pipeline, Postgres, Redis) to a Cloud VM and linking it to your frontend hosted on Vercel.

## 1. Deploy the Backend to a Cloud VM (AWS EC2, DigitalOcean, etc.)

Since the backend includes Docker containers, OpenCV processing, PostgreSQL, and Redis, it cannot run on Vercel. You need a dedicated Virtual Machine (VM).

### Step 1.1: Provision a VM
1. Go to your cloud provider (e.g., [DigitalOcean](https://www.digitalocean.com/), [AWS EC2](https://aws.amazon.com/ec2/), or [Google Cloud](https://cloud.google.com/compute)).
2. Create a new Droplet / Instance.
3. Choose **Ubuntu 22.04 LTS** (or 24.04).
4. Select a size with at least **2GB RAM** (4GB recommended for OpenCV video processing).
5. Add your SSH keys and create the instance.

### Step 1.2: Connect to the VM
Open your terminal and SSH into the machine using its public IP address:
```bash
ssh root@<YOUR_VM_IP>
```

### Step 1.3: Install Docker and Docker Compose
Run the following commands on the VM to install Docker:
```bash
# Update packages
apt-get update && apt-get upgrade -y

# Install Docker
apt-get install -y docker.io docker-compose git

# Enable Docker service
systemctl enable docker
systemctl start docker
```

### Step 1.4: Clone the Repository
Clone your project onto the VM:
```bash
git clone <YOUR_GITHUB_REPO_URL> purplle-store-intelligence
cd purplle-store-intelligence
```
*(If the repo is private, you may need to generate an SSH key on the VM or use a Personal Access Token).*

### Step 1.5: Start the Backend Services
Run Docker Compose in detached mode to build and start the API, Database, Redis, and Video Pipeline:
```bash
docker-compose up -d --build
```

### Step 1.6: Verify the Services
Ensure all containers are running properly:
```bash
docker-compose ps
```
You can check logs if anything failed:
```bash
docker-compose logs -f api
docker-compose logs -f pipeline
```

### Step 1.7: Open Firewall Ports
If you are using AWS or Google Cloud, ensure you open port **8000** in your VPC Security Group / Firewall settings to allow external traffic to the FastAPI backend.
If using `ufw` on the VM directly:
```bash
ufw allow 8000
ufw allow 22
ufw enable
```

---

## 2. Deploy the Frontend to Vercel

Now that your backend is running at `http://<YOUR_VM_IP>:8000`, you need to deploy the React dashboard to Vercel and tell it where the API is.

### Step 2.1: Deploy to Vercel
1. Push your repository to GitHub.
2. Go to [Vercel](https://vercel.com/) and click **Add New Project**.
3. Import your GitHub repository.
4. **Important**: Set the Framework Preset to **Vite** (Vercel usually detects this automatically).
5. Set the Root Directory to `dashboard` (since the frontend code is in the `dashboard` folder).

### Step 2.2: Configure Environment Variables
Before clicking Deploy (or in the Project Settings if already deployed):
1. Find the **Environment Variables** section.
2. Add the following variable:
   - **Key**: `VITE_API_URL`
   - **Value**: `http://<YOUR_VM_IP>:8000` (Replace `<YOUR_VM_IP>` with the public IP of your VM).

> **Note on HTTPS:** If your Vercel app is served over HTTPS (which it is), most browsers will block requests to an `http://` API due to Mixed Content policies. For a production-ready setup, you should point a domain to your VM's IP and set up a reverse proxy (like Nginx or Caddy) with an SSL certificate using Let's Encrypt. For hackathon testing, you can use the `http://` IP, but you may need to allow insecure content in your browser settings temporarily.

### Step 2.3: Deploy
Click **Deploy**. Vercel will build and host your React application. Once done, visit the Vercel URL, and it will fetch data directly from your Cloud VM's API!
