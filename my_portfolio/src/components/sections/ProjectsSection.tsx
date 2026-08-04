import { useState } from "react";
import { Project } from "@/data/projects";
import { ProjectCard } from "@/components/ProjectCard";
import { ProjectModal } from "@/components/ProjectModal";
import { normalizeImageList, normalizeStringList, usePortfolioSection } from "@/lib/tracknode";

type PortfolioProject = Project & {
  techStack: unknown[];
  images: unknown[];
};

export function ProjectsSection() {
  const content = usePortfolioSection<{
    title?: string;
    accent?: string;
    description?: string;
    categories?: Array<{ id: string; label: string }>;
    projects?: PortfolioProject[];
  }>("projects");
  const [activeCategory, setActiveCategory] = useState("all");
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const categories = content.categories || [];
  const projects = (content.projects || []).map((project) => ({
    ...project,
    techStack: normalizeStringList(project.techStack),
    images: normalizeImageList(project.images),
  })) as Project[];

  const filteredProjects = activeCategory === "all"
    ? projects
    : projects.filter((p) => p.category === activeCategory);

  return (
    <section id="projects" className="section-padding bg-card/30">
      <div className="section-container">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            {content.title} <span className="text-gold">{content.accent}</span>
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            {content.description}
          </p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap justify-center gap-2 mb-10">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`px-5 py-2.5 rounded-full text-sm font-medium border ${
                activeCategory === category.id
                  ? "filter-active"
                  : "border-border text-muted-foreground"
              }`}
            >
              {category.label}
            </button>
          ))}
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onViewDetails={setSelectedProject}
            />
          ))}
        </div>

        {/* Project Modal */}
        {selectedProject && (
          <ProjectModal
            project={selectedProject}
            onClose={() => setSelectedProject(null)}
          />
        )}
      </div>
    </section>
  );
}
