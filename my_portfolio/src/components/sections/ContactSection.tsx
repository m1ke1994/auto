import { Mail, Github, MessageCircle, Instagram, Linkedin } from "lucide-react";
import { resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";
import { Button } from "@/components/ui/button";
import { useContactModal } from "@/components/ContactModal";

const contactIcons = {
  github: Github,
  instagram: Instagram,
  linkedin: Linkedin,
  mail: Mail,
  message: MessageCircle,
};

export function ContactSection() {
  const content = usePortfolioSection<{
    title?: string;
    description?: string;
    contact_image?: string;
    contact_image_alt?: string;
    contacts?: Array<{ icon?: string; label: string; value: string; href: string }>;
  }>("contact");
  const contacts = content.contacts || [];
  const getContactIcon = (icon?: string) => contactIcons[icon as keyof typeof contactIcons] || Mail;
  const contactImage = resolveMediaUrl(content.contact_image);
  const { openContactModal } = useContactModal();

  return (
    <section id="contact" className="section-padding">
      <div className="section-container">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            {content.title}
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            {content.description}
          </p>
          <Button
            type="button"
            onClick={() => openContactModal()}
            className="mt-6 h-12 rounded-full bg-foreground px-8 text-base text-background hover:bg-foreground/90"
          >
            Связаться
          </Button>
        </div>

        <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-[minmax(0,1fr)_320px] md:items-start">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {contacts.map((contact) => {
              const Icon = getContactIcon(contact.icon);
              return (
              <a
                key={contact.label}
                href={contact.href}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-4 p-4 rounded-xl bg-card border border-border/50 hover:border-accent/30 hover:shadow-sm transition-all"
              >
                <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center">
                  <Icon className="h-5 w-5 text-gold" />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{contact.label}</p>
                  <p className="font-medium">{contact.value}</p>
                </div>
              </a>
              );
            })}
          </div>
          {contactImage ? (
            <img
              src={contactImage}
              alt={content.contact_image_alt || content.title || "Contacts"}
              className="w-full rounded-2xl border border-border object-cover shadow-premium"
            />
          ) : null}
        </div>
      </div>
    </section>
  );
}
