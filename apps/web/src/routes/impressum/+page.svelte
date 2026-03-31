<script lang="ts">
</script>

<svelte:head>
	<title>Impressum - InferenceBrake</title>
</svelte:head>

<div class="legal-page">
	<div class="legal-content">
		<h1>Impressum</h1>

		<p class="last-updated">Legal disclosure pursuant to § 5 TMG (German Telemedia Act)</p>

		<h2>Service Operator</h2>
		<div class="contact-info">
			<p><strong>Name:</strong> Vincent Mathis</p>
			<p><strong>Address:</strong> Loni-Franz-Straße 14</p>
			<p><strong>Postal Code & City:</strong> 65510 Idstein</p>
			<p><strong>Country:</strong> Germany</p>
			<p><strong>Email:</strong> <a href="mailto:admin@vincentmathis.xyz">admin@vincentmathis.xyz</a></p>
		</div>

		<h2>Business Type</h2>
		<p>
			Sole proprietorship (Einzelunternehmer). This business is not registered in a commercial
			register (Handelsregister).
		</p>
		<p>
			<!-- Tax and VAT info will be added when going live with payments -->
		</p>

		<h2>Responsible for Content</h2>
		<p>
			Vincent Mathis, Loni-Franz-Straße 14, 65510 Idstein, Germany<br />
			(pursuant to § 55 para. 2 RStV)
		</p>

		<h2>EU Online Dispute Resolution</h2>
		<p>
			The European Commission provides a platform for online dispute resolution (ODR):
			<a href="https://ec.europa.eu/consumers/odr/" target="_blank" rel="noopener noreferrer">
				https://ec.europa.eu/consumers/odr/
			</a>
		</p>
		<p>
			We are neither obligated nor willing to participate in dispute resolution proceedings
			before a consumer arbitration board.
		</p>

		<h2>Disclaimer</h2>
		<p>
			The content of this website has been created with care. However, we cannot guarantee
			the accuracy, completeness, or timeliness of the information provided. As a service
			provider, we are responsible for our own content on these pages pursuant to § 7 para. 1
			TMG. However, pursuant to §§ 8 to 10 TMG, we are not obligated to monitor transmitted
			or stored third-party information or to investigate circumstances indicating illegal
			activity. Obligations to remove or block content under general law remain unaffected.
			Liability in this regard is only possible from the point at which a specific legal
			violation becomes known.
		</p>

		<h2>Copyright</h2>
		<p>
			Content and works on this website created by the site operator are subject to German
			copyright law. Reproduction, processing, distribution, or any commercialization of
			such material beyond the scope of copyright law requires prior written consent.
			Downloads and copies are permitted for private, non-commercial use only.
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
		margin-bottom: 1rem;
	}

	a {
		color: var(--accent);
	}

	a:hover {
		text-decoration: underline;
	}
</style>