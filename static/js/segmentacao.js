/**
 * SIPAC - Módulo de Segmentação de Participantes
 * Gerencia a adição, remoção, reordenação de segmentos na interface
 * e a renderização dinâmica dos gráficos Chart.js por segmento.
 */

document.addEventListener("DOMContentLoaded", function () {
    // ----------------------------------------------------
    // 1. Cores e Constantes Globais
    // ----------------------------------------------------
    const COLORS = {
        primary: "#198754",
        primaryHover: "#146c43",
        blue: "#0d6efd",
        pink: "#d63384",
        teal: "#20c997",
        orange: "#fd7e14",
        purple: "#6f42c1",
        gray: "#6c757d",
        lightGray: "#e9ecef",
        genero: {
            Masculino: "#0d6efd",
            Feminino: "#d63384",
            "Não Informado": "#6c757d",
        },
        comunidade: {
            Sim: "#198754",
            Não: "#6c757d",
            "Não Informado": "#ced4da",
        },
    };

    // ----------------------------------------------------
    // 2. Manipulação Dinâmica de Segmentos (DOM)
    // ----------------------------------------------------
    const container = document.getElementById("segments-container");
    const btnAdd = document.getElementById("btn-add-segment");
    const form = document.getElementById("form-segmentacao");
    const payloadInput = document.getElementById("segments-payload");
    const template = document.getElementById("segment-template");

    function reindexSegments() {
        if (!container) return;
        const cards = container.querySelectorAll(".segment-card");
        const total = cards.length;

        cards.forEach((card, index) => {
            const order = index + 1;
            const badge = card.querySelector(".segment-order-badge");
            if (badge) {
                badge.textContent = `Prioridade #${order}`;
            }

            const btnUp = card.querySelector(".btn-move-up");
            const btnDown = card.querySelector(".btn-move-down");
            const btnRemove = card.querySelector(".btn-remove-segment");

            if (btnUp) btnUp.disabled = index === 0;
            if (btnDown) btnDown.disabled = index === total - 1;
            if (btnRemove) btnRemove.disabled = total <= 1;
        });
    }

    if (container) {
        container.addEventListener("click", function (e) {
            const target = e.target.closest("button");
            if (!target) return;

            const card = target.closest(".segment-card");
            if (!card) return;

            if (target.classList.contains("btn-move-up")) {
                const prev = card.previousElementSibling;
                if (prev) {
                    container.insertBefore(card, prev);
                    reindexSegments();
                }
            } else if (target.classList.contains("btn-move-down")) {
                const next = card.nextElementSibling;
                if (next) {
                    container.insertBefore(next, card);
                    reindexSegments();
                }
            } else if (target.classList.contains("btn-remove-segment")) {
                const total = container.querySelectorAll(".segment-card").length;
                if (total > 1) {
                    if (confirm("Deseja realmente remover este segmento?")) {
                        card.remove();
                        reindexSegments();
                    }
                } else {
                    alert("A análise requer pelo menos um segmento configurado.");
                }
            }
        });
    }

    if (btnAdd && template && container) {
        btnAdd.addEventListener("click", function () {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector(".segment-card");
            const nextOrder = container.querySelectorAll(".segment-card").length + 1;
            const uniqueId = "seg_" + Date.now();

            card.setAttribute("data-seg-id", uniqueId);
            const nameInput = card.querySelector(".segment-name-input");
            if (nameInput) {
                nameInput.value = `Segmento ${nextOrder}`;
            }

            container.appendChild(card);
            reindexSegments();
            card.scrollIntoView({ behavior: "smooth", block: "nearest" });
        });
    }

    if (form) {
        form.addEventListener("submit", function (e) {
            const cards = container.querySelectorAll(".segment-card");
            const segmentsData = [];

            cards.forEach((card, index) => {
                const segId = card.getAttribute("data-seg-id") || `seg_${index + 1}`;
                const nameInput = card.querySelector(".segment-name-input");
                const name = nameInput ? nameInput.value.trim() || `Segmento ${index + 1}` : `Segmento ${index + 1}`;

                const getVal = (selector) => {
                    const el = card.querySelector(selector);
                    return el ? el.value.trim() : "";
                };

                segmentsData.push({
                    id: segId,
                    name: name,
                    order: index + 1,
                    filters: {
                        tipo_participante: getVal(".filter-tipo"),
                        meta: getVal(".filter-meta"),
                        frente: getVal(".filter-frente"),
                        estado: getVal(".filter-estado"),
                        ano: getVal(".filter-ano"),
                        genero: getVal(".filter-genero"),
                        comunidade: getVal(".filter-comunidade"),
                        busca: getVal(".filter-busca"),
                    },
                });
            });

            if (payloadInput) {
                payloadInput.value = JSON.stringify(segmentsData);
            }
        });
    }

    // Inicializa botões e índices da visualização inicial
    reindexSegments();

    // ----------------------------------------------------
    // 3. Renderização dos Gráficos Chart.js por Segmento
    // ----------------------------------------------------
    const dataElement = document.getElementById("segmentacao-data");
    if (!dataElement) return;

    let analysisData;
    try {
        analysisData = JSON.parse(dataElement.textContent);
    } catch (e) {
        console.error("SIPAC: Erro ao interpretar JSON de segmentação:", e);
        return;
    }

    if (!analysisData || !Array.isArray(analysisData.segments)) return;
    if (typeof Chart === "undefined") {
        console.warn("SIPAC: Chart.js não está carregado.");
        return;
    }

    analysisData.segments.forEach((seg) => {
        if (seg.is_empty) return;

        const segId = seg.id;
        const charts = seg.charts || {};

        // 3.1 Gráfico de Gênero (Doughnut)
        const canvasGenero = document.getElementById(`chart-genero-${segId}`);
        if (canvasGenero && charts.genero) {
            const dataGen = charts.genero;
            const bgColors = (dataGen.labels || []).map(
                (lbl) => COLORS.genero[lbl] || COLORS.gray
            );

            new Chart(canvasGenero, {
                type: "doughnut",
                data: {
                    labels: dataGen.labels && dataGen.labels.length > 0 ? dataGen.labels : ["Sem dados"],
                    datasets: [
                        {
                            data: dataGen.data && dataGen.data.length > 0 ? dataGen.data : [1],
                            backgroundColor: bgColors.length > 0 ? bgColors : [COLORS.gray],
                            borderWidth: 2,
                            borderColor: "#ffffff",
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "60%",
                    plugins: {
                        legend: { position: "bottom", labels: { boxWidth: 12, padding: 8 } },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    const val = ctx.parsed;
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                    return ` ${ctx.label}: ${val.toLocaleString("pt-BR")} pessoas (${pct}%)`;
                                },
                            },
                        },
                    },
                },
            });
        }

        // 3.2 Gráfico de Comunidade Tradicional (Doughnut)
        const canvasComunidade = document.getElementById(`chart-comunidade-${segId}`);
        if (canvasComunidade && charts.comunidade) {
            const dataCom = charts.comunidade;
            const bgColors = (dataCom.labels || []).map(
                (lbl) => COLORS.comunidade[lbl] || COLORS.gray
            );

            new Chart(canvasComunidade, {
                type: "doughnut",
                data: {
                    labels: dataCom.labels && dataCom.labels.length > 0 ? dataCom.labels : ["Sem dados"],
                    datasets: [
                        {
                            data: dataCom.data && dataCom.data.length > 0 ? dataCom.data : [1],
                            backgroundColor: bgColors.length > 0 ? bgColors : [COLORS.gray],
                            borderWidth: 2,
                            borderColor: "#ffffff",
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "60%",
                    plugins: {
                        legend: { position: "bottom", labels: { boxWidth: 12, padding: 8 } },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    const val = ctx.parsed;
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                    return ` ${ctx.label}: ${val.toLocaleString("pt-BR")} pessoas (${pct}%)`;
                                },
                            },
                        },
                    },
                },
            });
        }

        // 3.3 Gráfico de Participantes por Estado (Bar)
        const canvasEstado = document.getElementById(`chart-estado-${segId}`);
        if (canvasEstado && charts.estado) {
            const dataEst = charts.estado;

            new Chart(canvasEstado, {
                type: "bar",
                data: {
                    labels: dataEst.labels && dataEst.labels.length > 0 ? dataEst.labels : ["Sem dados"],
                    datasets: [
                        {
                            label: "Participantes Únicos",
                            data: dataEst.data && dataEst.data.length > 0 ? dataEst.data : [0],
                            backgroundColor: "rgba(25, 135, 84, 0.8)",
                            hoverBackgroundColor: COLORS.primaryHover,
                            borderRadius: 4,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function (ctx) {
                                    return ` Participantes: ${ctx.parsed.y.toLocaleString("pt-BR")}`;
                                },
                            },
                        },
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { precision: 0 },
                            grid: { color: "rgba(0, 0, 0, 0.05)" },
                        },
                        x: { grid: { display: false } },
                    },
                },
            });
        }
    });
});
