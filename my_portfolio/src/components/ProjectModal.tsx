import { X, ExternalLink, Github, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Project } from "@/data/projects";

interface ProjectModalProps {
  project: Project | null;
  onClose: () => void;
}

export function ProjectModal({ project, onClose }: ProjectModalProps) {
  if (!project) return null;
  const primaryImage = project.images[0] || "";
  const imageAlt = project.image_alt || project.title;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[90vh] overflow-auto bg-card rounded-2xl shadow-premium-lg border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-10 h-10 rounded-full bg-background/80 backdrop-blur-sm flex items-center justify-center hover:bg-background transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Image */}
        <div className="aspect-video bg-muted">
          {primaryImage ? (
            <img
              src={primaryImage}
              alt={imageAlt}
              className="w-full h-full object-cover"
            />
          ) : null}
        </div>

        {/* Content */}
        <div className="p-6 md:p-8">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">{project.title}</h2>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mb-6">
            {project.techStack.map((tech) => (
              <span
                key={tech}
                className="text-sm px-3 py-1 rounded-full bg-secondary text-secondary-foreground"
              >
                {tech}
              </span>
            ))}
          </div>

          {/* Description */}
          <div className="space-y-6 mb-8">
            <div>
              <h3 className="font-semibold text-lg mb-2">Задача и решение</h3>
              <p className="text-muted-foreground leading-relaxed">
                {project.fullDescription}
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-lg mb-2">Моя роль</h3>
              <p className="text-muted-foreground leading-relaxed">
                {project.role}
              </p>
            </div>

            {project.results && (
              <div className="flex items-start gap-3 p-4 rounded-xl bg-accent/10 border border-accent/20">
                <CheckCircle className="h-5 w-5 text-gold mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold mb-1">Результат</h3>
                  <p className="text-sm text-muted-foreground">{project.results}</p>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            {project.demoUrl && (
              <Button asChild className="rounded-full">
                <a href={project.demoUrl} target="_blank" rel="noreferrer">
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Открыть демо
                </a>
              </Button>
            )}
            {project.repoUrl && (
              <Button variant="outline" asChild className="rounded-full">
                <a href={project.repoUrl} target="_blank" rel="noreferrer">
                  <Github className="h-4 w-4 mr-2" />
                  Исходный код
                </a>
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
