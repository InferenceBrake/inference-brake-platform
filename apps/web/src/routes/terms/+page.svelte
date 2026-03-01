<script lang="ts">
</script>

<svelte:head>
	<title>Terms of Service - InferenceBrake</title>
</svelte:head>

<div class="legal-page">
	<div class="legal-content">
		<h1>Terms of Service</h1>
		
		<p class="last-updated">Last updated: March 2026</p>

		<h2>1. Acceptance of Terms</h2>
		<p>By accessing and using InferenceBrake ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by these terms, please do not use this Service.</p>

		<h2>2. Description of Service</h2>
		<p>InferenceBrake provides an API service that detects when AI agents get stuck in reasoning loops. The Service includes:</p>
		<ul>
			<li>Loop detection through multiple detection methods</li>
			<li>API access for integrating loop detection into your applications</li>
			<li>Dashboard for monitoring usage and session history</li>
			<li>Webhooks for real-time alerts</li>
		</ul>

		<h2>3. User Accounts</h2>
		<p>To use the Service, you must create an account. You agree to:</p>
		<ul>
			<li>Provide accurate and complete registration information</li>
			<li>Maintain the security of your account and API key</li>
			<li>Promptly notify us of any unauthorized use of your account</li>
			<li>Be responsible for all activities that occur under your account</li>
		</ul>

		<h2>4. API Usage and Limits</h2>
		<p>Your subscription plan includes daily API check limits:</p>
		<ul>
			<li><strong>Hobby Plan</strong>: 100 checks per day</li>
			<li><strong>Pro Plan</strong>: 10,000 checks per day</li>
		</ul>
		<p>We reserve the right to suspend or terminate accounts that exceed these limits or abuse the Service.</p>

		<h2>5. Payment Terms</h2>
		<p>Subscription fees are billed monthly in advance. Payment is processed via Stripe. By providing payment information, you authorize us to charge the applicable fees to your payment method.</p>
		
		<p>Subscription fees are non-refundable. You may cancel your subscription at any time through your dashboard.</p>

		<h2>6. Data and Privacy</h2>
		<p>You retain full ownership of your data submitted to the Service. By using the Service, you grant us permission to process your data solely for the purpose of providing the Service.</p>
		
		<p>For information about how we handle your data, please refer to our <a href="/privacy">Privacy Policy</a>.</p>

		<h2>7. Acceptable Use</h2>
		<p>You agree not to use the Service to:</p>
		<ul>
			<li>Violate any applicable laws or regulations</li>
			<li>Infringe upon the rights of any third party</li>
			<li>Attempt to gain unauthorized access to the Service or its systems</li>
			<li>Interfere with or disrupt the Service</li>
			<li>Use the Service for any illegal or unauthorized purpose</li>
			<li>Resell or redistribute the Service without authorization</li>
		</ul>

		<h2>8. Intellectual Property</h2>
		<p>The Service and its original content, features, and functionality are and will remain the exclusive property of InferenceBrake and its licensors. The Service is protected by copyright, trademark, and other laws.</p>

		<h2>9. Limitation of Liability</h2>
		<p>IN NO EVENT SHALL INFERENCEBRAKE BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING WITHOUT LIMITATION, LOSS OF PROFITS, DATA, USE, GOODWILL, OR OTHER INTANGIBLE LOSSES, RESULTING FROM:</p>
		<ul>
			<li>YOUR ACCESS TO OR USE OF OR INABILITY TO ACCESS OR USE THE SERVICE</li>
			<li>ANY CONDUCT OR CONTENT OF ANY THIRD PARTY ON THE SERVICE</li>
			<li>ANY CONTENT OBTAINED FROM THE SERVICE</li>
			<li>UNAUTHORIZED ACCESS, USE, OR ALTERATION OF YOUR TRANSMISSIONS OR CONTENT</li>
		</ul>

		<h2>10. Disclaimer</h2>
		<p>THE SERVICE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS. INFERENCEBRAKE MAKES NO REPRESENTATIONS OR WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, AS TO THE OPERATION OF THE SERVICE, OR THE INFORMATION, CONTENT, OR MATERIALS INCLUDED THEREIN. YOU EXPRESSLY AGREE THAT YOUR USE OF THESE SERVICES, THEIR CONTENT, AND ANY SERVICES OR ITEMS OBTAINED FROM US IS AT YOUR SOLE RISK.</p>

		<h2>11. Termination</h2>
		<p>We may terminate or suspend your account and access to the Service immediately, without prior notice or liability, for any reason, including breach of these Terms.</p>
		
		<p>Upon termination, your right to use the Service will immediately cease. If you wish to terminate your account, you may simply discontinue using the Service or delete your account through the dashboard.</p>

		<h2>12. Governing Law</h2>
		<p>These Terms shall be governed and construed in accordance with the laws of Germany, without regard to its conflict of law provisions.</p>

		<h2>13. Changes to Terms</h2>
		<p>We reserve the right, at our sole discretion, to modify or replace these Terms at any time. We will provide notice of any significant changes.</p>

		<h2>14. Contact Us</h2>
		<p>If you have any questions about these Terms, please contact us at [your@email.com].</p>

		<p class="note"><strong>Note:</strong> This terms of service is a template and should be reviewed by a legal professional to ensure compliance with your specific situation and any applicable laws.</p>
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

	.note {
		margin-top: 2rem;
		padding: 1rem;
		background: rgba(249, 115, 22, 0.1);
		border: 1px solid rgba(249, 115, 22, 0.3);
		border-radius: var(--radius-md);
		font-size: 0.9rem;
	}
</style>
