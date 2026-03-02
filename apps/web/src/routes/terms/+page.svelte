<script lang="ts">
</script>

<svelte:head>
	<title>Terms of Service - InferenceBrake</title>
</svelte:head>

<div class="legal-page">
	<div class="legal-content">
		<h1>Terms of Service</h1>

		<p class="last-updated">Last updated: March 2026</p>

		<h2>1. Parties and Scope</h2>
		<p>
			These Terms of Service govern your use of InferenceBrake, operated by Vincent Mathis,
			Loni-Franz-Straße 14, 65510 Idstein, Germany ("we", "us", or "our").
		</p>
		<p>
			This service is intended exclusively for businesses, developers, and other commercial
			users (B2B). It is not intended for consumers as defined under German consumer
			protection law (§ 13 BGB).
		</p>
		<p>
			By registering an account, you confirm that you are acting in a commercial or
			professional capacity and agree to these Terms.
		</p>

		<h2>2. Description of Service</h2>
		<p>InferenceBrake provides an API service for detecting reasoning loops in AI agent systems. The service includes:</p>
		<ul>
			<li>Loop detection via semantic, action-based, and n-gram detectors</li>
			<li>API access for integrating loop detection into your applications</li>
			<li>Dashboard for monitoring usage and session history</li>
			<li>Webhook alerts (Pro plan)</li>
		</ul>
		<p>
			We provide the service on a best-effort basis and do not guarantee any specific
			detection accuracy or false-positive rate. The service is a monitoring aid,
			not a safety-critical system.
		</p>

		<h2>3. Plans and Pricing</h2>
		<p>The following plans are available:</p>
		<ul>
			<li><strong>Hobby (free):</strong> 1,000 API checks per day, basic detectors, 7-day session history.</li>
			<li><strong>Pro ($9/month):</strong> 10,000 API checks per day, all detectors, configurable thresholds, webhook alerts, 90-day history.</li>
		</ul>
		<p>
			We reserve the right to change plan features and pricing with 30 days' notice by email.
			Existing subscriptions remain at the current price until the end of the paid period.
		</p>

		<h2>4. Account Registration</h2>
		<p>To use the service, you must create an account. You agree to:</p>
		<ul>
			<li>Provide accurate and complete registration information</li>
			<li>Keep your account credentials and API key secure</li>
			<li>Notify us promptly of any unauthorized use of your account</li>
			<li>Take responsibility for all activity that occurs under your account</li>
		</ul>

		<h2>5. Payment Terms</h2>
		<p>
			Paid plans are billed monthly in advance via Stripe. By subscribing, you authorize
			Stripe to charge the applicable fees to your payment method on a recurring basis.
		</p>
		<p>
			All prices are net prices. As a small business operator under § 19 UStG
			(Kleinunternehmerregelung), we do not charge VAT. No VAT will appear on invoices
			or Stripe receipts.
		</p>
		<p>
			If a payment fails, we reserve the right to downgrade or suspend access to the
			paid plan until payment is resolved.
		</p>

		<h2>6. Cancellation and Refunds</h2>
		<p>
			You may cancel your subscription at any time from your dashboard settings.
			After cancellation, you retain access until the end of the current billing period.
			We do not offer partial refunds for unused time.
		</p>
		<p>
			We reserve the right to terminate accounts in violation of these Terms without
			refund (see Section 8).
		</p>

		<h2>7. Acceptable Use</h2>
		<p>You may not use the service to:</p>
		<ul>
			<li>Make automated API calls without genuine use in an AI agent system (abuse)</li>
			<li>Submit personal data of third parties as reasoning traces without a lawful basis</li>
			<li>Reverse engineer, decompile, or circumvent rate limits</li>
			<li>Resell or sublicense the service without prior written authorization</li>
			<li>Violate any applicable laws or regulations</li>
		</ul>

		<h2>8. Termination</h2>
		<p>
			We may suspend or terminate your account immediately and without prior notice
			if you violate these Terms, abuse the service, or if required by law.
			In the event of termination for cause, no refund will be issued.
		</p>
		<p>
			You may terminate your account at any time by deleting it from your dashboard settings.
		</p>

		<h2>9. Availability</h2>
		<p>
			We aim for high availability but do not provide a legally binding uptime guarantee (SLA).
			Planned maintenance will be announced where possible. Outages caused by third-party
			infrastructure (Supabase, Vercel, Stripe) are outside our control.
		</p>

		<h2>10. Limitation of Liability</h2>
		<p>
			We are fully liable for intent (Vorsatz) and gross negligence (grobe Fahrlässigkeit),
			and for damages arising from injury to life, body, or health.
		</p>
		<p>
			For ordinary negligence, we are only liable for breach of a material contractual
			obligation (Kardinalpflicht). In such cases, liability is limited to foreseeable,
			typical damages, and in no event exceeding the amount you paid for the service
			in the 12 months preceding the claim.
		</p>
		<p>
			We accept no liability for detection errors (false positives or false negatives)
			and any resulting damage to your AI agent system. We are also not liable for
			indirect damages, lost profits, or data loss, to the extent permitted by law.
		</p>

		<h2>11. Data and Privacy</h2>
		<p>
			You retain full ownership of the data you submit to the service. You grant us
			a limited license to process that data solely to provide the service.
			We do not use your data to train AI models.
		</p>
		<p>
			For full details on data handling, see our <a href="/privacy">Privacy Policy</a>.
		</p>

		<h2>12. Intellectual Property</h2>
		<p>
			The service, its codebase, design, and all associated content are the exclusive
			property of the operator or its licensors. Using the service does not grant you
			any ownership or license rights beyond what is necessary to use the API as described.
		</p>

		<h2>13. Changes to These Terms</h2>
		<p>
			We may update these Terms with 30 days' notice by email. If you do not object
			within 30 days of receiving notice, the updated Terms are considered accepted.
			The notice will explicitly state your right to object and the consequences of silence.
		</p>

		<h2>14. Governing Law and Jurisdiction</h2>
		<p>
			These Terms are governed exclusively by German law, excluding the UN Convention
			on Contracts for the International Sale of Goods (CISG).
		</p>
		<p>
			As this service is B2B only, the place of jurisdiction for all disputes arising
			from this contract is Idstein, Germany.
		</p>

		<h2>15. Severability</h2>
		<p>
			If any provision of these Terms is found to be invalid or unenforceable, the
			remaining provisions remain in full force. The invalid provision will be replaced
			by one that most closely reflects the original intent.
		</p>

		<h2>16. Contact</h2>
		<p>
			For questions about these Terms, contact us at
			<a href="mailto:legal@inferencebrake.com">legal@inferencebrake.com</a>.
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
</style>