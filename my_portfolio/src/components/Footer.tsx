import { Github, Send, Mail, Instagram } from "lucide-react";
import { resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";

const socialIcons = {
  github: Github,
  instagram: Instagram,
  mail: Mail,
  message: Send,
};

export function Footer() {
  const content = usePortfolioSection<{
    logo_text?: string;
    logo_image?: string;
    description?: string;
    nav_title?: string;
    contact_title?: string;
    nav_items?: Array<{ label: string; href: string }>;
    social_links?: Array<{ icon?: string; href: string; label: string }>;
    copyright?: string;
  }>("footer");
  const currentYear = new Date().getFullYear();
  const navLinks = content.nav_items || [];
  const socialLinks = content.social_links || [];
  const getSocialIcon = (icon?: string) => socialIcons[icon as keyof typeof socialIcons] || Mail;
  const logoImage = resolveMediaUrl(content.logo_image);

  return (
    <footer className="border-t border-border bg-card/50">
      <div className="section-container py-12 md:py-16">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
          {/* Brand */}
          <div>
            <a href="#" className="font-display font-bold text-xl tracking-tight inline-block mb-4">
              {logoImage ? (
                <img src={logoImage} alt={content.logo_text || "Portfolio"} className="h-9 max-w-[180px] object-contain" />
              ) : (
                <>
                  <span className="text-gold">{"<"}</span>
                  {content.logo_text}
                  <span className="text-gold">{" />"}</span>
                </>
              )}
            </a>
            <p className="text-muted-foreground text-sm max-w-xs">
              {content.description}
            </p>
          </div>

          {/* Navigation */}
          <div>
            <h4 className="font-display font-semibold mb-4">{content.nav_title}</h4>
            <ul className="space-y-2">
              {navLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors text-sm"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Social */}
          <div>
            <h4 className="font-display font-semibold mb-4">{content.contact_title}</h4>
            <div className="flex items-center gap-3">
              {socialLinks.map((social) => {
                const Icon = getSocialIcon(social.icon);
                return (
                <a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/10 transition-all"
                  aria-label={social.label}
                >
                  <Icon className="h-5 w-5" />
                </a>
                );
              })}
            </div>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-12 pt-8 border-t border-border text-center">
          <p className="text-muted-foreground text-sm">
            © {currentYear} {content.copyright}{" "}
            <span className="text-gold">♥</span>
          </p>
        </div>
      </div>
    </footer>
  );
}
