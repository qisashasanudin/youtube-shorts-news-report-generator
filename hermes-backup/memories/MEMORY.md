Shorts pipeline: 50-150w all-caps ASS narration; no Firecrawl; TikTok-first 4/d 08-22; YT score≥75 only. Scheduler must stay automated and broad: never hardcode game titles; prefer generic FPS/TPS/news query stems; filter results after fetching; reject category/index URLs; write exactly 10 real stories to scheduler_output.json.
§
User preference: Use tmpfiles.org for all video/file deliveries to Discord and Telegram instead of native uploads (native Discord upload may fail silently). Upload via: curl -F "file=@<path>" https://tmpfiles.org/api/v1/upload
§
Cron job model override UX: the `cronjob` tool with action='update' rejects setting model/provider to null ("No updates provided"). If you want a job to inherit the main config default, use the CLI path `hermes cron edit <job-id>` and remove the explicit model/provider there. Also avoid adding explicit cron model overrides unless the job truly needs a different model.
§
Scheduler: 4x daily at 9/13/17/21, 10 stories to Discord; primary search now ddgs/CDP before Firecrawl; file delivery via tmpfiles.org.
§
Web research workflow: Use ddgs search (already default in config) to find candidate URLs, then use terminal + curl to fetch raw HTML, then execute_code with BeautifulSoup/lxml to parse and extract clean content. No Firecrawl, gateway, or CDP required. Skill created: local-html-extraction.
§
Memory backup process generates files in /Users/qisashasanudin/repositories/youtube-shorts-news-report-generator/hermes-backup. Upon completion of this local backup, a subsequent automated step must execute to push all contents of the 'hermes-backup' folder remotely, ensuring that the most current state is mirrored offsite.
§
To bypass YouTube 403/Forbidden errors for restricted content, prioritize using specific headers (Desktop User-Agent, Referer) and the `player_client` configuration discovered in the Media Pipeline workflow.
§
User requires all content generation (like Shorts) to include a subtitle option when executing the build script. The current script usage error suggests this is a required input parameter for video creation workflows.