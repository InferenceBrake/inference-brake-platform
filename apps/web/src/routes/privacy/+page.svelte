<script lang="ts">
</script>

<svelte:head>
	<title>Privacy Policy - InferenceBrake</title>
</svelte:head>

<div class="legal-page">
	<div class="legal-content">
		<h1>Privacy Policy</h1>
		
		<p class="last-updated">Last updated: March 2026</p>

		<h2>1. Introduction</h2>
		<p>InferenceBrake ("we", "us", or "our") operates the InferenceBrake service. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our service.</p>

		<p>Please read this privacy policy carefully. If you do not agree with the terms of this privacy policy, please do not access the service.</p>

		<h2>2. Data We Collect</h2>
		
		<h3>Personal Data</h3>
		<p>While using our service, we may ask you to provide us with certain personally identifiable information that can be used to contact or identify you. Personally identifiable information may include:</p>
		<ul>
			<li>Email address</li>
			<li>First and last name</li>
			<li>Usage data (API usage, session data)</li>
		</ul>

		<h3>Agent Session Data</h3>
		<p>When you use our API to detect loops in AI agent conversations, we process:</p>
		<ul>
			<li>Conversation steps/messages</li>
			<li>Agent actions and responses</li>
			<li>Metadata (session IDs, timestamps)</li>
		</ul>
		<p>This data is processed solely for the purpose of loop detection and is not used for any other purpose.</p>

		<h2>3. How We Use Your Data</h2>
		<p>We use the collected data for:</p>
		<ul>
			<li>Providing and maintaining our service</li>
			<li>Notifying you about changes to our service</li>
			<li>Providing customer support</li>
			<li>Monitoring the usage of our service</li>
			<li>Processing payments (via Stripe)</li>
			<li>Enforcing our terms and conditions</li>
		</ul>

		<h2>4. Data Retention</h2>
		<p>We will retain your personal data only for as long as is necessary for the purposes set out in this Privacy Policy. We will retain and use your personal data to the extent necessary to comply with our legal obligations (for example, if we are required to retain your data to comply with applicable laws), resolve disputes, and enforce our legal agreements and policies.</p>
		
		<p>Your agent session data is retained according to your plan:</p>
		<ul>
			<li>Hobby plan: 7 days</li>
			<li>Pro plan: 90 days</li>
		</ul>

		<h2>5. Data Sharing</h2>
		<p>We may share your data with:</p>
		<ul>
			<li><strong>Supabase</strong> (Database & Authentication): We use Supabase for data storage and user authentication. Data is processed in compliance with GDPR.</li>
			<li><strong>Stripe</strong> (Payment Processing): Payment information is processed directly by Stripe. We do not store your credit card information.</li>
			<li><strong>Vercel</strong> (Hosting): Our web application is hosted on Vercel, which processes necessary technical data.</li>
		</ul>

		<h2>6. Data Security</h2>
		<p>We use appropriate technical and organizational security measures to protect your personal data. However, no method of transmission over the Internet or electronic storage is 100% secure, and we cannot guarantee absolute security.</p>

		<h2>7. Your Rights (GDPR)</h2>
		<p>If you are a resident of the European Economic Area (EEA), you have certain data protection rights:</p>
		<ul>
			<li><strong>Right to Access</strong>: You have the right to request copies of your personal data.</li>
			<li><strong>Right to Rectification</strong>: You can request that we correct any information you believe is inaccurate.</li>
			<li><strong>Right to Erasure</strong>: You can request that we erase your personal data ("right to be forgotten").</li>
			<li><strong>Right to Restrict Processing</strong>: You can request that we restrict the processing of your data.</li>
			<li><strong>Right to Data Portability</strong>: You can request that we transfer your data to another organization.</li>
			<li><strong>Right to Object</strong>: You can object to our processing of your data.</li>
		</ul>
		<p>To exercise any of these rights, please contact us at [your@email.com].</p>

		<h2>8. Cookies</h2>
		<p>We use essential cookies for authentication and session management. These are necessary for the proper functioning of our service and do not require your consent under GDPR (they are "technically necessary").</p>

		<h2>9. Third-Party Services</h2>
		<p>We may use third-party Service Providers to monitor and analyze the use of our Service:</p>
		<ul>
			<li><strong>Supabase</strong>: <a href="https://supabase.com/privacy">Privacy Policy</a></li>
			<li><strong>Stripe</strong>: <a href="https://stripe.com/privacy">Privacy Policy</a></li>
			<li><strong>Vercel</strong>: <a href="https://vercel.com/legal/privacy-policy">Privacy Policy</a></li>
		</ul>

		<h2>10. Children's Privacy</h2>
		<p>Our service is not intended for use by children under the age of 13. We do not knowingly collect personally identifiable information from children under 13.</p>

		<h2>11. Changes to This Privacy Policy</h2>
		<p>We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "last updated" date.</p>

		<h2>12. Contact Us</h2>
		<p>If you have any questions about this Privacy Policy, please contact us:</p>
		<ul>
			<li>By email: [your@email.com]</li>
		</ul>

		<p class="note"><strong>Note:</strong> This privacy policy is a template and should be reviewed by a legal professional to ensure compliance with your specific situation and any applicable laws.</p>
	</div>
</div>

<style>
	.legal-page {
		min-height: 100vh;
		padding: 4rem 2rem;
		background: var(--bg-primary);
	}

	.legal-content {
		max-width: 800px;
		margin: 0 auto;
	}

	h1 {
		font-size: 2rem;
		margin-bottom: 1rem;
	}

	h2 {
		font-size: 1.25rem;
		margin-top: 2rem;
		margin-bottom: 1rem;
		color: var(--text-primary);
	}

	h3 {
		font-size: 1.1rem;
		margin-top: 1.5rem;
		margin-bottom: 0.75rem;
		color: var(--text-primary);
	}

	.last-updated {
		color: var(--text-secondary);
		margin-bottom: 2rem;
		font-size: 0.9rem;
	}

	p {
		line-height: 1.7;
		color: var(--text-secondary);
		margin-bottom: 1rem;
	}

	ul {
		margin-left: 1.5rem;
		margin-bottom: 1rem;
	}

	li {
		line-height: 1.7;
		color: var(--text-secondary);
		margin-bottom: 0.5rem;
	}

	a {
		color: var(--accent);
	}

	a:hover {
		text-decoration: underline;
	}

	.note {
		margin-top: 2rem;
		padding: 1rem;
		background: rgba(249, 115, 22, 0.1);
		border: 1px solid rgba(249, 115, 22, 0.3);
		border-radius: var(--radius-md);
		font-size: 0.9rem;
	}
</style>
