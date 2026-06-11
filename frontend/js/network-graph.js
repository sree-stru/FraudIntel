/* ===================================================================
   FraudNetworkGraph — Apache ECharts "Cyber Threat" Map
   =================================================================== */

class FraudNetworkGraph {

  static TYPE_COLORS = {
    account:  "#ff0000",
    device:   "#ff3333",
    ip_address: "#cc0000",
    ip:       "#cc0000",
    phone:    "#ff6666",
    email:    "#990000",
    merchant: "#ff1a1a",
    beneficiary: "#e60000",
    default:  "#ff4d4d",
  };

  constructor(containerId) {
    this.containerId = containerId;
    this.container = document.getElementById(containerId);
    this.chart = null;
    this.worldGeoJson = null;
    this.resizeListener = () => { if (this.chart) this.chart.resize(); };
    window.addEventListener('resize', this.resizeListener);
  }

  async render(data) {
    if (!data || !data.nodes || !data.edges) {
      console.warn("Invalid data for FraudNetworkGraph", data);
      return;
    }
    
    if (!this.chart) {
      // Set up cyber grid background
      this.container.innerHTML = "";
      this.container.style.width = "100%";
      this.container.style.height = "100%";
      this.container.style.background = "#050505";
      this.container.style.backgroundImage = `
        linear-gradient(rgba(255, 0, 0, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 0, 0, 0.05) 1px, transparent 1px)
      `;
      this.container.style.backgroundSize = "50px 50px";

      this.chart = echarts.init(this.container);
    }

    // Load GeoJSON if not loaded
    if (!this.worldGeoJson) {
      try {
        const res = await fetch('js/world.json');
        this.worldGeoJson = await res.json();
        echarts.registerMap('world', this.worldGeoJson);
      } catch (err) {
        console.error("Failed to load world.json", err);
        console.log("Network Graph Edges:", data.edges);
        return;
      }
    }

    const nodesData = [];
    const coordMap = {}; // id -> [lng, lat]

    // Generate deterministic coordinates for nodes across the globe
    data.nodes.forEach(n => {
      let hash = 0;
      for (let i = 0; i < n.id.length; i++) {
        hash = n.id.charCodeAt(i) + ((hash << 5) - hash);
      }
      
      // Keep coordinates roughly within populated continents (avoid poles and middle of oceans)
      const lng = -120 + (Math.abs(hash * 31) % 240); // -120 to 120
      const lat = -40 + (Math.abs(hash * 17) % 100);  // -40 to 60

      coordMap[n.id] = [lng, lat];
      
      const color = FraudNetworkGraph.TYPE_COLORS[n.type] || FraudNetworkGraph.TYPE_COLORS.default;

      nodesData.push({
        name: n.id,
        value: [lng, lat, n.risk_score || 50], // [lng, lat, value]
        itemStyle: { color: color },
        type: n.type,
        risk: n.risk_score || 'N/A'
      });
    });

    const linesData = [];
    data.edges.forEach(e => {
      const sourceId = typeof e.source === 'object' ? e.source.id : e.source;
      const targetId = typeof e.target === 'object' ? e.target.id : e.target;
      
      const sourceCoord = coordMap[sourceId];
      const targetCoord = coordMap[targetId];
      
      if (sourceCoord && targetCoord) {
        linesData.push({
          coords: [sourceCoord, targetCoord],
          edgeData: e, // Store full edge info for the formatter
          lineStyle: {
            color: '#ff1a1a',
            width: 1.5,
            opacity: 0.4,
            curveness: 0.2 // curved arcs
          }
        });
      }
    });

    const option = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(26, 0, 0, 0.8)',
        borderColor: '#ff1a1a',
        textStyle: { color: '#ff1a1a', fontFamily: '"Share Tech Mono", monospace' },
        formatter: function (params) {
          if (params.seriesType === 'effectScatter') {
            return `
              <strong style="font-size:14px;text-shadow:0 0 5px #ff1a1a">${params.data.name}</strong><br/>
              Type: ${params.data.type.toUpperCase()}<br/>
              Risk Score: ${params.data.risk}
            `;
          } else if (params.seriesType === 'lines') {
            return `Link: <strong>${params.data.value}</strong>`;
          }
        }
      },
      geo: {
        map: 'world',
        roam: true,
        zoom: 1.2,
        itemStyle: {
          areaColor: '#000000',     // pitch black land
          borderColor: '#ff1a1a',   // neon red borders
          borderWidth: 0.5,
          shadowColor: 'rgba(255, 26, 26, 0.3)',
          shadowBlur: 5
        },
        emphasis: {
          itemStyle: { areaColor: '#1a0000' },
          label: { show: false }
        }
      },
      series: [
        {
          name: 'Entities',
          type: 'effectScatter',
          coordinateSystem: 'geo',
          zlevel: 2,
          rippleEffect: {
            brushType: 'stroke',
            scale: 4
          },
          label: {
            show: true,
            position: 'right',
            formatter: '{b}',
            textStyle: { color: '#ff4d4d', fontSize: 10, fontFamily: '"Share Tech Mono", monospace', textShadowBlur: 2, textShadowColor: '#ff1a1a' }
          },
          symbolSize: function (val) {
            return 6 + (val[2] / 20); // Scale by risk score
          },
          itemStyle: {
            shadowBlur: 10,
            shadowColor: '#ff1a1a'
          },
          data: nodesData
        },
        {
          name: 'Connections',
          type: 'lines',
          coordinateSystem: 'geo',
          zlevel: 1,
          effect: {
            show: true,
            period: 4,
            trailLength: 0.4,
            color: '#ffffff',
            symbolSize: 3
          },
          lineStyle: {
            color: '#ff1a1a',
            width: 1,
            opacity: 0.2,
            curveness: 0.2
          },
          label: {
            show: true,
            position: 'middle',
            formatter: function(params) {
              const e = params.data.edgeData || {};
              const relText = e.relationship || e.relationship_type || e.type || e.label || e.description || "related";
              return relText.replace(/_/g, ' ').toUpperCase();
            },
            textStyle: {
              color: '#ff4d4d',
              fontSize: 10,
              fontFamily: '"Share Tech Mono", monospace',
              textShadowBlur: 2,
              textShadowColor: '#000000'
            }
          },
          data: linesData
        }
      ]
    };

    this.chart.setOption(option);
  }

  destroy() {
    window.removeEventListener('resize', this.resizeListener);
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
    if (this.container) {
      this.container.innerHTML = "";
      this.container.style.backgroundImage = "none";
    }
  }
}
