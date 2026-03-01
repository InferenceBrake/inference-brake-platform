<script lang="ts">
</script>

<svelte:head>
	<title>Impressum - InferenceBrake</title>
</svelte:head>

<div class="legal-page">
	<div class="legal-content">
		<h1>Impressum</h1>
		
		<p class="last-updated">Last updated: March 2026</p>

		<h2>Information according to § 5 TMG</h2>

		<div class="contact-info">
			<p><strong>Name:</strong> [Your Name]</p>
			<p><strong>Address:</strong> [Your Street Address]</p>
			<p><strong>Postal Code & City:</strong> [Your Postal Code, City]</p>
			<p><strong>Country:</strong> Germany</p>
			<p><strong>Email:</strong> [your@email.com]</p>
			<p><strong>Phone:</strong> [Your Phone Number]</p>
		</div>

		<h2>Commercial Register</h2>
		<p>This is a sole proprietorship (Einzelunternehmer) registered in Germany.</p>

		<h2>Responsible for Content</h2>
		<p>[Your Name]</p>
		<p>Contact: [your@email.com]</p>

		<h2>Disclaimer</h2>
		<p>The content of this website was created with utmost care. However, I cannot guarantee the accuracy, completeness, or timeliness of the provided information. As a service provider, I am responsible for my own content on these pages according to § 7 para.1 TMG. However, according to §§ 8 to 10 TMG, I am not obligated to monitor transmitted or stored third-party information or to investigate circumstances that indicate illegal activity.</p>

		<p>Obligations to remove or block the use of information under general law remain unaffected. However, liability in this regard is only possible from the point in time at which a concrete infringement of the law becomes known. If I become aware of any such infringements, I will remove the relevant content immediately.</p>

		<h2>Copyright</h2>
		<p>The content and works created by the site operator on these pages are subject to German copyright law. The reproduction, processing, distribution, or any form of commercialization of such material beyond the scope of the copyright law shall require the prior written consent of its respective author or creator.</p>

		<p>Downloads and copies of this site are only permitted for private, non-commercial use.</p>

		<p>If the content on this site was not created by the operator, the copyrights of third parties are respected. In particular, third-party content will be identified as such. Should you nevertheless become aware of a copyright infringement, please inform me accordingly. If I become aware of any infringements, I will remove such content immediately.</p>
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

	.contact-info {
		background: var(--bg-secondary);
		border: 1px solid var(--border);
		border-radius: var(--radius-md);
		padding: 1.5rem;
		margin: 1.5rem 0;
	}

	.contact-info p {
		margin-bottom: 0.5rem;
	}

	p {
		line-height: 1.7;
		color: var(--text-secondary);
	}
</style>
