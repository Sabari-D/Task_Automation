# Production Deployment Guide: Vercel & AWS

This guide covers how to deploy the Auto-Worker engine in a production-ready environment using Vercel for the Next.js frontend and AWS (App Runner / EC2) for the FastAPI backend, PostgreSQL, and Redis infrastructure.

## 1. Frontend: Deploying to Vercel

Vercel is the native platform for Next.js applications and provides optimal performance out of the box.

### Steps
1. Push your repository to GitHub, GitLab, or Bitbucket.
2. Log in to [Vercel](https://vercel.com/) and click **Add New Project**.
3. Import your repository and select the `frontend/` folder as the Root Directory.
4. **Environment Variables**:
   Add the following environment variables during the Vercel project setup:
   - `NEXT_PUBLIC_API_URL` -> Base URL of your backend (e.g., `https://api.yourdomain.com`)
   - `NEXT_PUBLIC_WS_URL` -> WebSocket URL of your backend (e.g., `wss://api.yourdomain.com`)
5. Click **Deploy**. Vercel will automatically detect Next.js and build it.

---

## 2. Backend: Deploying to AWS App Runner

AWS App Runner provides an easy way to run containers without managing infrastructure, perfect for scaling our FastAPI backend.

### Prerequisites
- Create an Amazon RDS PostgreSQL instance.
- Create an Amazon ElastiCache for Redis instance.
- Ensure your `backend/` directory is packaged as a Docker container.

### Steps
1. **Push your Docker image**:
   Push the backend Dockerfile to Amazon ECR (Elastic Container Registry).
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
   docker build -t auto-worker-api ./backend
   docker tag auto-worker-api:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/auto-worker-api:latest
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/auto-worker-api:latest
   ```

2. **Create App Runner Service**:
   - Go to AWS App Runner > Create an App Runner service.
   - Choose **Container Registry** > Amazon ECR and select the uploaded image.
   - Set Port to `8000`.
   - **Environment Variables**: Add your production DB, Redis, and Groq keys:
     - `DATABASE_URL` = `postgresql+asyncpg://user:pass@RDS_ENDPOINT:5432/aw_db`
     - `REDIS_URL` = `redis://ELASTICACHE_ENDPOINT:6379/0`
     - `GROQ_API_KEY` = `your_groq_api_key`
   - Finish and deploy. Your API will receive an `awsapprunner.com` URL.

*(Note: Use this App Runner URL for your Vercel `NEXT_PUBLIC_API_URL`)*

---

## Alternative: Deploying to AWS EC2 (Docker Compose)

If you prefer keeping everything in one server (simpler but less scalable), you can deploy using the provided `docker-compose.yml`.

### Steps
1. Launch an Ubuntu EC2 instance (t3.small or larger recommended due to LLM memory footprints) and open ports `80`, `443`, `8000`, and `3000`.
2. Connect to the instance and install Docker & Git.
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/auto-worker.git
   cd auto-worker
   ```
4. Set up your `.env` file with production keys.
5. Launch the stack:
   ```bash
   sudo docker compose up -d --build
   ```
6. Secure with Nginx/LetsEncrypt to enable HTTPS/WSS (strongly advised for WebSockets).
