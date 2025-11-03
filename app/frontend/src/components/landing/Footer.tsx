export function Footer() {
  const socialLinks = [
    { name: "Twitter/X", url: "#", icon: "𝕏" },
    { name: "Discord", url: "#", icon: "💬" },
    { name: "GitHub", url: "#", icon: "⚙️" },
  ];

  return (
    <footer className="py-12 px-6 bg-pantheon-cosmic-bg border-t border-pantheon-border">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {/* Brand */}
          <div>
            <div className="flex items-center space-x-2 mb-4">
              <img
                src="/logo.jpeg"
                alt="Crypto Pantheon Logo"
                className="w-8 h-8 rounded object-cover"
              />
              <span className="text-xl font-mythic font-bold text-pantheon-text-primary">
                Pantheon Elite
              </span>
            </div>
            <p className="text-sm text-pantheon-text-secondary">
              Legendary AI councils for superior crypto trading strategies
            </p>
          </div>

          {/* Social */}
          <div>
            <h4 className="text-sm font-semibold text-pantheon-text-primary uppercase tracking-wider mb-4">
              Community
            </h4>
            <div className="flex space-x-4">
              {socialLinks.map((social) => (
                <a
                  key={social.name}
                  href={social.url}
                  className="w-10 h-10 rounded-full bg-pantheon-cosmic-surface border border-pantheon-border flex items-center justify-center text-xl hover:border-pantheon-primary-500 hover:bg-pantheon-primary-500/10 transition-all"
                  aria-label={social.name}
                >
                  {social.icon}
                </a>
              ))}
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="pt-8 border-t border-pantheon-border text-center">
          <p className="text-sm text-pantheon-text-secondary">
            © {new Date().getFullYear()} Pantheon Elite. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
