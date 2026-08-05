import { ExternalLink } from "lucide-react";
import { resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";

export function CasesSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    description?: string;
    cases?: Array<{ id?: string; title?: string; summary?: string; image?: string; image_alt?: string; link?: string; results?: string }>;
  }>("cases");
  const cases = content.cases || [];
  if (!cases.length) return null;

  return (
    <section className="section-padding">
      <div className="section-container">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">{content.description}</p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {cases.map((item, index) => {
            const image = resolveMediaUrl(item.image);
            return (
              <article key={item.id || `${item.title}-${index}`} className="card-premium overflow-hidden">
                {image ? <img src={image} alt={item.image_alt || item.title || ""} className="h-56 w-full object-cover" /> : null}
                <div className="p-6">
                  <h3 className="mb-3 text-xl font-semibold">{item.title}</h3>
                  <p className="text-sm leading-relaxed text-muted-foreground">{item.summary}</p>
                  {item.results ? <p className="mt-4 text-sm font-medium text-foreground">{item.results}</p> : null}
                  {item.link ? (
                    <a href={item.link} target="_blank" rel="noreferrer" className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-foreground">
                      <ExternalLink className="h-4 w-4" />
                      Open case
                    </a>
                  ) : null}
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
