# Prompts for GPT-4o classifications

POST_CLASSIFICATION_PROMPT = """
Analyze the following post and provide a classification in this exact format:
sentiment: [positive/negative/neutral], theme: [brief description], format_suitability: [suitable/not_suitable]

Post: {post_text}

Return only the classification line, no additional text.
"""

PROFILE_CLASSIFICATION_PROMPT = """
Analyze the following user profile information and classify the user in a short descriptive phrase, like "Luxury buyer, prefers floral scents".

Profile: {profile_text}

Return only the classification phrase, no additional text.
"""

BLOG_GENERATION_PROMPT = """
Based on the following relevant data retrieved from our knowledge base, write a comprehensive blog post about the topic: {query}.

Relevant Data:
{data}

The blog post should be engaging, informative, and around 800-1000 words. Include an introduction, body with sections, and a conclusion. Use markdown formatting for headings.
"""

SOCIAL_SNIPPET_GENERATION_PROMPT = """
Based on the following relevant data, create a concise and engaging social media snippet (tweet/thread or post) about the topic: {query}.

Relevant Data:
{data}

The snippet should be under 280 characters for Twitter, or suitable for other platforms. Make it catchy and include a call to action if appropriate.
"""

B2B_EMAIL_GENERATION_PROMPT = """
Based on the following relevant data, write a professional B2B pitch email about the topic: {query}.

Relevant Data:
{data}

The email should include a subject line, greeting, body with value proposition, and a call to action. Keep it concise and persuasive.
"""
