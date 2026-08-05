import { ExternalLink } from "lucide-react";
import { Project } from "@/data/projects";

interface ProjectCardProps {
  project: Project;
  onViewDetails: (project: Project) => void;
}

export function ProjectCard({ project, onViewDetails }: ProjectCardProps) {
  const primaryImage = project.images[0] || "";
  const imageAlt = project.image_alt || project.title;
  const trackProjectClick = () => {
    if (project.demoUrl === "https://tracknode.ru/") {
      window.tracknode?.track?.("tracknode_project_click", {
        source_site: "portfolio",
        destination: project.demoUrl,
        placement: "project_card",
        page_path: window.location.pathname,
      });
    }
  };

  return (
    <div
      className="project-card card-premium overflow-hidden cursor-pointer transition-transform duration-200 ease-out hover:scale-[1.03] hover:shadow-md"
      role="button"
      tabIndex={0}
      onClick={() => onViewDetails(project)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onViewDetails(project);
        }
      }}
    >
      {/* Image */}
      <div className="aspect-video relative overflow-hidden bg-muted">
        {primaryImage ? (
          <img
            src={primaryImage}
            alt={imageAlt}
            className="w-full h-full object-cover"
          />
        ) : null}
      </div>

      {/* Content */}
      <div className="p-5 md:p-6">
        <h3 className="font-semibold text-lg mb-2 line-clamp-1">{project.title}</h3>
        <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
          {project.shortDescription}
        </p>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {project.techStack.slice(0, 4).map((tech) => (
            <span
              key={tech}
              className="text-xs px-2 py-1 rounded-md bg-secondary text-secondary-foreground"
            >
              {tech}
            </span>
          ))}
          {project.techStack.length > 4 && (
            <span className="text-xs px-2 py-1 rounded-md bg-secondary text-secondary-foreground">
              +{project.techStack.length - 4}
            </span>
          )}
        </div>

        {project.demoUrl && (
          <a
            href={project.demoUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-medium text-foreground"
            onClick={(event) => {
              event.stopPropagation();
              trackProjectClick();
            }}
          >
            <ExternalLink className="h-4 w-4" />
            Посмотреть проект
          </a>
        )}
      </div>
    </div>
  );
}
