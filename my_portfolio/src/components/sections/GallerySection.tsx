import { resolveMediaUrl, usePortfolioSection } from "@/lib/tracknode";

export function GallerySection() {
  const content = usePortfolioSection<{
    title?: string;
    description?: string;
    images?: Array<{ id?: string; image?: string; image_alt?: string; caption?: string }>;
  }>("gallery");
  const images = (content.images || []).map((item) => ({ ...item, resolved: resolveMediaUrl(item.image) })).filter((item) => item.resolved);
  if (!images.length) return null;

  return (
    <section className="section-padding bg-card/30">
      <div className="section-container">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold md:text-4xl">{content.title}</h2>
          <p className="mx-auto max-w-2xl text-lg text-muted-foreground">{content.description}</p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {images.map((item, index) => (
            <figure key={item.id || `${item.resolved}-${index}`} className="overflow-hidden rounded-2xl border border-border bg-card">
              <img src={item.resolved} alt={item.image_alt || item.caption || ""} className="aspect-video w-full object-cover" />
              {item.caption ? <figcaption className="p-4 text-sm text-muted-foreground">{item.caption}</figcaption> : null}
            </figure>
          ))}
        </div>
      </div>
    </section>
  );
}
