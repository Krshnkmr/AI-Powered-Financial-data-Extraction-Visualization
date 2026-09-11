# AI-Powered-Financial-data-Extraction-Visualization
The repository is used to push the financial data files in image format and then it can automatically store it in to the Mongo DB and it pushed to grafana. So we can see the financial data in visual format.

**🚀 Challenging myself to build, learn, and adapt with AI!**

Even when we don't get the immediate chance to work on a specific stack in our daily projects, I firmly believe in learning by doing. Every massive system built today started as a tiny, hands-on experiment.

To challenge my skills in Observability and Data Pipelines, I leveraged AI to accelerate my development workflow—shifting my focus entirely toward architectural decision-making.

I successfully built an automated pipeline designed to transform raw corporate financial media into interactive visual insights. Here is how the **workflow operates:**

**1️⃣ User Interface:** A custom-built UI handles uploading financial document images along with specific company metadata.

**2️⃣ Data Extraction:** Integrated with Google AI Studio (Gemini) to read, parse, and structure unstructured financial terms (like Revenue, EPS, etc.) directly from the images.

**3️⃣ Storage Layer: **Stored dynamically in MongoDB, choosing it for its efficient disk space footprint via WiredTiger compression, easy data schema mapping, and quick initial configuration.

**4️⃣ Observability & Analytics:** Connected to Grafana to translate hard financial numbers into clear, scannable visual charts so stakeholders can instantly interpret organization health.

**⚠️ Engineering Challenges Overcome:**

**Data Integration:** Connecting open-source MongoDB to Grafana can be tricky, as the native connector is locked behind Grafana Enterprise.

**The Workaround:** I initially tried a standard JSON API plugin, but ran into performance limitations. Ultimately, I implemented the Grafana Infinity Data Source plugin to cleanly fetch the BSON/JSON data directly into the dashboard.
I would love to hear your thoughts on this architecture or how you approach open-source data visualization! 👇

