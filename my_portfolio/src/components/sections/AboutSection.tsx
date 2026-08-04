import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { Code2, RefreshCw, Plug, Bot, Server } from "lucide-react";
import { usePortfolioSection } from "@/lib/tracknode";

const serviceIcons = {
  bot: Bot,
  code: Code2,
  plug: Plug,
  refresh: RefreshCw,
  server: Server,
};

export function AboutSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    paragraphs?: Array<{ text: string }>;
    services_title?: string;
    services?: Array<{ icon?: string; title: string; description: string }>;
  }>("about");
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const services = content.services || [];
  const getServiceIcon = (icon?: string) => serviceIcons[icon as keyof typeof serviceIcons] || Code2;

  return (
    <section id="about" className="section-padding bg-card/30">
      <div className="section-container" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="max-w-3xl mb-16"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <div className="space-y-4 text-muted-foreground text-lg leading-relaxed">
            {(content.paragraphs || []).map((paragraph) => (
              <p key={paragraph.text}>{paragraph.text}</p>
            ))}
          </div>
        </motion.div>

        {/* Services */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <h3 className="text-xl font-semibold mb-8">{content.services_title}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map((service, index) => {
              const Icon = getServiceIcon(service.icon);
              return (
              <motion.div
                key={service.title}
                initial={{ opacity: 0, y: 20 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.4, delay: 0.3 + index * 0.1 }}
                className="card-premium p-6 hover-lift group"
              >
                <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:bg-accent/20 transition-colors">
                  <Icon className="h-6 w-6 text-gold" />
                </div>
                <h4 className="font-semibold mb-2">{service.title}</h4>
                <p className="text-sm text-muted-foreground">{service.description}</p>
              </motion.div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
