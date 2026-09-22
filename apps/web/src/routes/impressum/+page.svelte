<script lang="ts">
</script>

<svelte:head>
	<title>Impressum - InferenceBrake</title>
</svelte:head>

<div class="legal-brutal bg-base-100 text-base-content">
	<div class="mx-auto w-full max-w-3xl px-4 py-12 md:px-8 md:py-16">
		<h1>Impressum</h1>

		<p class="last-updated nb-muted font-mono text-xs font-bold tracking-widest uppercase">Legal disclosure pursuant to § 5 TMG (German Telemedia Act)</p>

		<h2>Service Operator</h2>
		<div class="nb-brutal my-6 bg-base-200 p-5">
			<p><strong>Name:</strong> Vincent Mathis</p>
			<p><strong>Address:</strong> Loni-Franz-Straße 14</p>
			<p><strong>Postal Code & City:</strong> 65510 Idstein</p>
			<p><strong>Country:</strong> Germany</p>
			<p><strong>Email:</strong> <a href="mailto:support@inferencebrake.dev">support@inferencebrake.dev</a></p>
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
	.legal-brutal {
		font-family: 'Outfit', sans-serif;
	}

	.legal-brutal h1 {
		font-size: 2.25rem;
		font-weight: 800;
		letter-spacing: -0.02em;
		color: var(--color-base-content);
		margin-bottom: 0.5rem;
	}

	.legal-brutal h2 {
		font-size: 1.5rem;
		font-weight: 800;
		color: var(--color-base-content);
		margin-top: 2.5rem;
		margin-bottom: 1rem;
	}

	.legal-brutal .last-updated {
		margin-bottom: 2.5rem;
	}

	.legal-brutal p {
		line-height: 1.7;
		margin-bottom: 1rem;
	}

	.legal-brutal .nb-brutal p:last-child {
		margin-bottom: 0;
	}

	.legal-brutal strong {
		color: var(--color-base-content);
	}

	.legal-brutal a {
		font-weight: 700;
		text-decoration: underline;
		text-underline-offset: 3px;
	}
</style>