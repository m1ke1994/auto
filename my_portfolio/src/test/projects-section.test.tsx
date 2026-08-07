import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProjectsSection } from "@/components/sections/ProjectsSection";
import { projects } from "@/data/projects";

describe("ProjectsSection", () => {
  it("uses landing as the default category and keeps all projects selectable", () => {
    render(<ProjectsSection />);

    const allProjectsButton = screen.getByRole("button", { name: "Все проекты" });
    const landingButton = screen.getByRole("button", { name: "Лендинги" });
    const landingProjects = projects.filter((project) => project.category === "landing");

    expect(landingButton).toHaveClass("filter-active");
    expect(allProjectsButton).not.toHaveClass("filter-active");
    expect(screen.getAllByRole("button")).toHaveLength(projects.length ? landingProjects.length + 4 : 4);
    expect(screen.getByText("Салон красоты")).toBeInTheDocument();
    expect(screen.queryByText("Smart Nara — витрина интернет-магазина")).not.toBeInTheDocument();

    fireEvent.click(allProjectsButton);
    expect(allProjectsButton).toHaveClass("filter-active");
    expect(screen.getByText("Smart Nara — витрина интернет-магазина")).toBeInTheDocument();
    expect(screen.getAllByRole("button")).toHaveLength(projects.length + 4);

    fireEvent.click(landingButton);
    expect(landingButton).toHaveClass("filter-active");
    expect(screen.getByText("Лендинг юриста")).toBeInTheDocument();
    expect(screen.queryByText("Smart Nara — витрина интернет-магазина")).not.toBeInTheDocument();
  });
});
