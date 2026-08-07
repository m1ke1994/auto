import { useMemo, useRef } from "react";
import { motion, useInView } from "framer-motion";
import {
  Activity,
  Bot,
  Briefcase,
  Bug,
  Code2,
  Download,
  FileCheck,
  Globe2,
  KeyRound,
  Layout,
  Network,
  Plug,
  Search,
  Server,
  Settings,
  Shield,
  Wrench,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  normalizePortfolioServices,
  PortfolioService,
  usePortfolioSection,
} from "@/lib/tracknode";
import { useContactModal } from "@/components/ContactModal";

const serviceIcons = {
  activity: Activity,
  bot: Bot,
  briefcase: Briefcase,
  bug: Bug,
  code: Code2,
  download: Download,
  "file-check": FileCheck,
  globe: Globe2,
  "globe-2": Globe2,
  key: KeyRound,
  layout: Layout,
  network: Network,
  plug: Plug,
  search: Search,
  server: Server,
  settings: Settings,
  shield: Shield,
  wrench: Wrench,
  zap: Zap,
};

export function ServicesSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    description?: string;
    services?: unknown[];
  }>("services");
  const services = normalizePortfolioServices(content.services);
  const groupedServices = useMemo(() => groupByCategory(services), [services]);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const { openContactModal } = useContactModal();

  if (!services.length) return null;

  return (
    <section id="services" className="section-padding">
      <div className="section-container" ref={ref}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
          className="mb-12 max-w-3xl"
        >
          <h2 className="text-3xl font-bold md:text-4xl">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">{content.description}</p>
        </motion.div>

        <div className="space-y-10">
          {Object.entries(groupedServices).map(([category, items]) => (
            <div key={category}>
              <h3 className="mb-4 text-xl font-semibold">{category}</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {items.map((service, index) => {
                  const Icon = serviceIcons[service.icon as keyof typeof serviceIcons] || Code2;
                  return (
                    <motion.article
                      key={service.id || service.title}
                      initial={{ opacity: 0, y: 20 }}
                      animate={isInView ? { opacity: 1, y: 0 } : {}}
                      transition={{ duration: 0.35, delay: index * 0.03 }}
                      className="card-premium flex min-h-48 flex-col p-5"
                    >
                      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-accent/10">
                        <Icon className="h-5 w-5 text-gold" />
                      </div>
                      <h4 className="font-semibold leading-snug">{service.title}</h4>
                      {service.description ? (
                        <p className="mt-2 flex-1 text-sm leading-6 text-muted-foreground">
                          {service.description}
                        </p>
                      ) : (
                        <div className="flex-1" />
                      )}
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => openContactModal(service.title)}
                        className="mt-5 h-10 rounded-full"
                      >
                        Оставить заявку
                      </Button>
                    </motion.article>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function groupByCategory(services: PortfolioService[]) {
  return services.reduce<Record<string, PortfolioService[]>>((groups, service) => {
    const category = service.category || "Услуги";
    groups[category] = groups[category] || [];
    groups[category].push(service);
    return groups;
  }, {});
}
