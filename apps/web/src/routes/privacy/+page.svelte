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
		<p>
			InferenceBrake is operated by Vincent Mathis, Loni-Franz-Straße 14, 65510 Idstein,
			Germany ("we", "us", or "our"). This Privacy Policy explains how we collect, use,
			and safeguard your data when you use InferenceBrake.
		</p>
		<p>
			We are subject to the EU General Data Protection Regulation (GDPR). The responsible
			controller within the meaning of the GDPR is the operator listed above.
		</p>

		<h2>2. Data We Collect</h2>

		<h3>Account Data</h3>
		<p>When you register, we collect:</p>
		<ul>
			<li>Email address</li>
			<li>Password (stored as a bcrypt hash — never readable by us)</li>
			<li>Account creation date and selected plan</li>
		</ul>
		<p>Legal basis: Art. 6(1)(b) GDPR — necessary to perform the contract with you.</p>

		<h3>API Usage Data</h3>
		<p>When you use the API, we process:</p>
		<ul>
			<li>API key (for authentication)</li>
			<li>Reasoning traces submitted for loop detection</li>
			<li>Session IDs and request timestamps</li>
			<li>Daily request counts (for rate limiting)</li>
			<li>Detection results (whether a loop was detected)</li>
		</ul>
		<p>
			Reasoning traces are stored and automatically deleted after 7 days (Hobby plan)
			or 90 days (Pro plan).
		</p>
		<p>Legal basis: Art. 6(1)(b) GDPR — necessary to perform the contract with you.</p>
		<div class="note">
			<strong>Note:</strong> Do not submit personal data of end users as reasoning traces.
			InferenceBrake is designed to monitor AI agent outputs, not to process end-user
			personal information.
		</div>

		<h3>Payment Data</h3>
		<div class="note">
			<strong>Note:</strong> Payments are not currently active. Paid plans will be
			introduced in the future.
		</div>
		<p>Payments are processed exclusively by Stripe. We only store:</p>
		<ul>
			<li>Stripe Customer ID</li>
			<li>Stripe Subscription ID</li>
			<li>Subscription status and current period end date</li>
		</ul>
		<p>
			Credit card numbers and full payment details are never stored on our servers.
			They are handled entirely by Stripe.
		</p>
		<p>Legal basis: Art. 6(1)(b) GDPR — necessary to perform the contract with you.</p>

		<h3>Server Logs</h3>
		<p>
			Our infrastructure providers (Supabase, Vercel) automatically log IP addresses,
			user agents, and request metadata for security and debugging purposes.
			These logs are retained for up to 30 days.
		</p>
		<p>Legal basis: Art. 6(1)(f) GDPR — legitimate interest in operating secure systems.</p>

		<h2>3. Data Sharing and Processors</h2>
		<p>We use the following sub-processors who handle data on our behalf:</p>
		<ul>
			<li>
				<strong>Supabase Inc.</strong> — Database, authentication, and edge functions.
				Data is processed in EU data centers (AWS Frankfurt).
				<a href="https://supabase.com/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
			</li>
			<li>
				<strong>Stripe Inc.</strong> — Payment processing and subscription management.
				Data transfer to the US is based on the EU-US Data Privacy Framework (Art. 45 GDPR).
				<a href="https://stripe.com/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
			</li>
			<li>
				<strong>Vercel Inc.</strong> — Frontend hosting.
				Data transfer to the US is based on Standard Contractual Clauses (Art. 46 GDPR).
				<a href="https://vercel.com/legal/privacy-policy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>
			</li>
		</ul>
		<p>We do not sell your data to third parties. We do not use your data to train AI models.</p>

		<h2>4. Data Retention</h2>
		<p>
			Reasoning traces and session data are deleted automatically according to your plan
			(7 or 90 days). When you delete your account, all personal data is deleted within
			30 days, except where we are required to retain it by law.
		</p>
		<p>
			Billing records and invoices are retained for 10 years to comply with German
			tax law (§ 147 AO). Stripe-side payment data is subject to Stripe's own
			retention policy.
		</p>

		<h2>5. Your Rights (GDPR)</h2>
		<p>If you are in the EEA, you have the following rights:</p>
		<ul>
			<li><strong>Right to access</strong> (Art. 15): Request a copy of your data.</li>
			<li><strong>Right to rectification</strong> (Art. 16): Correct inaccurate data.</li>
			<li><strong>Right to erasure</strong> (Art. 17): Request deletion of your data.</li>
			<li><strong>Right to restriction</strong> (Art. 18): Restrict how we process your data.</li>
			<li><strong>Right to data portability</strong> (Art. 20): Receive your data in a machine-readable format.</li>
			<li><strong>Right to object</strong> (Art. 21): Object to processing based on legitimate interests.</li>
		</ul>
		<p>
			To exercise any of these rights, contact us at
			<a href="mailto:admin@vincentmathis.xyz">admin@vincentmathis.xyz</a>.
			We will respond within 30 days.
		</p>
		<p>
			You also have the right to lodge a complaint with the supervisory authority in
			Hesse, Germany:
			<a href="https://www.datenschutz.hessen.de" target="_blank" rel="noopener noreferrer">
				Der Hessische Beauftragte für Datenschutz und Informationsfreiheit (HBDI)
			</a>
		</p>

		<h2>6. Cookies</h2>
		<p>
			InferenceBrake uses only technically necessary cookies for authentication
			(Supabase Auth session token). These are required for the service to function
			and do not require consent under § 25(2) TDDDG / Art. 5(3) ePrivacy Directive.
		</p>
		<p>We do not use tracking, advertising, or analytics cookies.</p>

		<h2>7. Data Security</h2>
		<p>
			All connections are TLS-encrypted. Passwords are hashed with bcrypt. API keys
			are generated with 64 bytes of cryptographic randomness. We recommend storing
			your API key securely and rotating it if you believe it has been compromised
			(available in your dashboard settings).
		</p>

		<h2>8. Changes to This Policy</h2>
		<p>
			We may update this Privacy Policy from time to time. For significant changes,
			we will notify registered users by email. The date at the top of this page
			reflects the most recent update.
		</p>

		<h2>9. Contact</h2>
		<p>
			For any privacy-related questions or to exercise your rights:
			<a href="mailto:admin@vincentmathis.xyz">admin@vincentmathis.xyz</a>
		</p>
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

	strong {
		color: var(--text-primary);
	}

	.note {
		margin-top: 0.5rem;
		padding: 1rem;
		background: rgba(249, 115, 22, 0.1);
		border: 1px solid rgba(249, 115, 22, 0.3);
		border-radius: var(--radius-md);
		font-size: 0.9rem;
		color: var(--text-secondary);
		line-height: 1.7;
		margin-bottom: 1rem;
	}
</style>