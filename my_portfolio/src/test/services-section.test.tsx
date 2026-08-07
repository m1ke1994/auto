import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ServicesSection } from "@/components/sections/ServicesSection";

describe("ServicesSection", () => {
  it("shows only the active TrackNode service category", () => {
    render(<ServicesSection />);

    expect(screen.getByRole("heading", { name: "Услуги" })).toBeInTheDocument();
    expect(screen.getByText("Разработка, администрирование и техническая помощь — выберите нужное направление.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Разработка" })).toHaveAttribute("aria-pressed", "true");

    expect(screen.getByRole("heading", { name: "Разработка сайта" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Автоматизация процессов" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Настройка сервера" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Оставить заявку" })).toHaveLength(6);

    fireEvent.click(screen.getByRole("button", { name: "Администрирование" }));
    expect(screen.getByRole("button", { name: "Администрирование" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("heading", { name: "Настройка сервера" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Резервное копирование" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Разработка сайта" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Оставить заявку" })).toHaveLength(6);

    fireEvent.click(screen.getByRole("button", { name: "Техническая помощь" }));
    expect(screen.getByRole("button", { name: "Техническая помощь" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("heading", { name: "КриптоПро и ЭЦП" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Диагностика и техническая помощь" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Настройка сервера" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Оставить заявку" })).toHaveLength(6);
  });
});
