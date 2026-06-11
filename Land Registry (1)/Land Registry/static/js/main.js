/**
 * Land Registry Management System - Client Side Scripting
 */

// Helper to format values as Indian Rupees
function formatINR(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(amount);
}

// 1. AJAX Detail Modal Handler
function showRecordDetails(recordId) {
    const modal = document.getElementById('details-modal');
    if (!modal) return;

    // Fetch record data from server JSON endpoint
    fetch(`/record/${recordId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Unable to fetch record details.");
            }
            return response.json();
        })
        .then(data => {
            // Populate Modal Fields
            document.getElementById('detail-owner').innerText = data.owner_name;
            document.getElementById('detail-father').innerText = data.father_husband_name;
            document.getElementById('detail-aadhaar').innerText = data.aadhaar_id;
            document.getElementById('detail-mobile').innerText = data.mobile_number;
            document.getElementById('detail-khasra').innerText = data.khasra_number;
            document.getElementById('detail-khata').innerText = data.khata_number;
            document.getElementById('detail-survey').innerText = data.survey_number;
            document.getElementById('detail-area').innerText = `${data.area} Hectares`;
            document.getElementById('detail-value').innerText = formatINR(data.market_value);
            document.getElementById('detail-village').innerText = data.village;
            document.getElementById('detail-tehsil').innerText = data.tehsil;
            document.getElementById('detail-district').innerText = data.district;
            document.getElementById('detail-state').innerText = data.state;
            document.getElementById('detail-pincode').innerText = data.pin_code;
            document.getElementById('detail-type').innerText = data.land_type;
            document.getElementById('detail-date').innerText = data.registration_date;
            document.getElementById('detail-remarks').innerText = data.remarks || 'No official remarks or active audits registered.';

            // Setup Download Button
            const downloadBtn = document.getElementById('modal-download-btn');
            if (downloadBtn) {
                downloadBtn.setAttribute('onclick', `downloadRecord(${data.id})`);
            }

            // Status Badge Formatting
            const statusEl = document.getElementById('detail-status');
            statusEl.innerText = data.registry_status;
            statusEl.className = 'details-value badge'; // Reset classes
            
            const statusClass = data.registry_status.toLowerCase();
            statusEl.classList.add(statusClass);

            // Display Modal
            modal.classList.add('active');
        })
        .catch(err => {
            alert(`Error: ${err.message}`);
        });
}

function hideDetailsModal() {
    const modal = document.getElementById('details-modal');
    if (modal) {
        modal.classList.remove('active');
    }
}

function closeDetailsModal(event) {
    if (event.target.id === 'details-modal') {
        hideDetailsModal();
    }
}

// 2. Delete Confirmation Prompt
function confirmDelete(ownerName) {
    return confirm(`CRITICAL ACTION WARNING:\n\nAre you sure you want to permanently delete the land registry record owned by "${ownerName}"?\n\nThis will purge all corresponding Khasra/Khata database records. This action cannot be undone.`);
}

// 3. Dashboard Chart.js Integration
function initializeDashboardCharts() {
    const typeCanvas = document.getElementById('typeChart');
    const districtCanvas = document.getElementById('districtChart');
    
    if (!typeCanvas || !districtCanvas) return;

    fetch('/api/dashboard/chart-data')
        .then(response => {
            if (!response.ok) {
                throw new Error("Could not fetch analytics data.");
            }
            return response.json();
        })
        .then(data => {
            // Chart 1: Land Type Distribution (Doughnut)
            const typeLabels = data.land_types.map(item => item.type);
            const typeCounts = data.land_types.map(item => item.count);
            
            new Chart(typeCanvas, {
                type: 'doughnut',
                data: {
                    labels: typeLabels,
                    datasets: [{
                        data: typeCounts,
                        backgroundColor: [
                            '#0284c7', // Agricultural - Blue
                            '#b45309', // Residential - Gold
                            '#10b981', // Commercial - Green
                            '#64748b'  // Industrial - Slate
                        ],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                boxWidth: 12,
                                font: {
                                    family: 'Inter',
                                    size: 11
                                },
                                color: '#475569'
                            }
                        }
                    },
                    cutout: '65%'
                }
            });

            // Chart 2: District Land Valuations (Bar)
            const districtLabels = data.districts.map(item => item.district);
            const districtValuations = data.districts.map(item => item.value);

            new Chart(districtCanvas, {
                type: 'bar',
                data: {
                    labels: districtLabels,
                    datasets: [{
                        label: 'Total Value (₹ Crores)',
                        data: districtValuations,
                        backgroundColor: 'rgba(2, 132, 199, 0.85)',
                        hoverBackgroundColor: '#0284c7',
                        borderRadius: 6,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                font: {
                                    family: 'Inter',
                                    size: 11
                                },
                                color: '#475569'
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(15, 23, 42, 0.05)'
                            },
                            ticks: {
                                font: {
                                    family: 'Inter',
                                    size: 11
                                },
                                color: '#475569'
                            }
                        }
                    }
                }
            });
        })
        .catch(err => {
            console.error("Dashboard Analytics Error:", err);
        });
}

// 4. Mock PDF Download
function downloadRecord(recordId) {
    if (!recordId) return;
    
    // Simulate generation delay
    const btn = event.currentTarget;
    const originalText = btn.innerHTML;
    btn.innerHTML = `<i data-lucide="loader" class="spin" style="width: 14px; height: 14px;"></i> Generating...`;
    btn.disabled = true;
    lucide.createIcons();

    setTimeout(() => {
        btn.innerHTML = `<i data-lucide="check" style="width: 14px; height: 14px;"></i> Downloaded`;
        lucide.createIcons();
        alert(`Official Deed PDF for Record ID #${recordId} has been successfully generated and downloaded to your device.`);
        
        setTimeout(() => {
            btn.innerHTML = originalText;
            btn.disabled = false;
            lucide.createIcons();
        }, 3000);
    }, 1500);
}
