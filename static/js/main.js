// Auth and generic frontend logic
document.addEventListener('DOMContentLoaded', () => {
    // Auth Form Submit
    const authForm = document.getElementById('auth-form');
    if (authForm) {
        authForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const msgEl = document.getElementById('auth-message');
            
            if (typeof isLogin !== 'undefined' && isLogin) {
                // Login
                try {
                    const res = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        localStorage.setItem('token', data.token);
                        localStorage.setItem('role', data.role);
                        window.location.href = data.role === 'admin' ? '/admin/dashboard' : 
                                              (data.role === 'hr' ? '/hr/dashboard' : '/dashboard');
                    } else {
                        msgEl.innerText = data.message || "Login failed";
                    }
                } catch(err) {
                    msgEl.innerText = "Error connecting to server.";
                }
            } else {
                // Register
                const name = document.getElementById('name').value;
                const role = document.getElementById('role').value;
                try {
                    const res = await fetch('/api/auth/register', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name, email, password, role })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        window.location.href = '/login';
                    } else {
                        msgEl.innerText = data.message || "Registration failed";
                    }
                } catch(err) {
                    msgEl.innerText = "Error connecting to server.";
                }
            }
        });
    }

    // Dashboard Load logic
    if (window.location.pathname === '/dashboard') {
        loadCandidateData();
    } else if (window.location.pathname === '/admin/dashboard') {
        loadAdminData();
    } else if (window.location.pathname === '/hr/dashboard') {
        loadHRData();
    }
});

function getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    window.location.href = '/';
}

function showTab(tabId, element) {
    document.querySelectorAll('.tab-content').forEach(el => el.style.display = 'none');
    document.getElementById(tabId + '-tab').style.display = 'block';
    
    document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
    if(element) element.classList.add('active');
}

async function loadCandidateData() {
    try {
        const res = await fetch('/api/candidate/profile', { headers: getAuthHeaders() });
        if (res.ok) {
            const profile = await res.json();
            document.getElementById('cand-name').innerText = profile.name;
            
            // Check if resume exists
            if (profile.resume_path) {
                document.getElementById('resume-analysis').style.display = 'block';
                document.getElementById('ats-score').innerText = 'Data available';
                document.getElementById('skills-list').innerText = profile.skills || 'N/A';
                document.getElementById('strengths-list').innerText = 'Data available';
            }
        } else {
            window.location.href = '/login';
            return;
        }

        // Fetch Interviews
        const intRes = await fetch('/api/candidate/interviews', { headers: getAuthHeaders() });
        if (intRes.ok) {
            const interviews = await intRes.json();
            const completed = interviews.filter(i => i.status === 'completed');
            
            document.getElementById('comp-interviews').innerText = completed.length;
            if (completed.length > 0) {
                const totalScore = completed.reduce((sum, i) => sum + (i.overall_rating || 0), 0);
                document.getElementById('avg-score').innerText = (totalScore / completed.length).toFixed(1);
            }
            
            const listDiv = document.getElementById('interviews-list');
            if (interviews.length === 0) {
                listDiv.innerHTML = '<p style="padding:1.5rem;">No interviews found. Start one from the Overview tab.</p>';
            } else {
                listDiv.innerHTML = `
                    <table style="width:100%; text-align:left; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 2px solid var(--gray);">
                                <th style="padding:10px;">ID</th>
                                <th style="padding:10px;">Date</th>
                                <th style="padding:10px;">Status</th>
                                <th style="padding:10px;">Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${interviews.map(i => `
                                <tr>
                                    <td style="padding:10px; border-bottom:1px solid #e2e8f0;">#${i.id}</td>
                                    <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${i.scheduled_at ? new Date(i.scheduled_at).toLocaleDateString() : 'N/A'}</td>
                                    <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${i.status}</td>
                                    <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${i.overall_rating || 'N/A'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
        }
    } catch(err) { console.error(err); }

    // Setup Resume Upload
    const resumeForm = document.getElementById('resume-form');
    if (resumeForm) {
        resumeForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fileInput = document.getElementById('resumeFile');
            const photoInput = document.getElementById('photoFile');
            const btn = document.getElementById('upload-btn');
            
            const formData = new FormData();
            formData.append('resume', fileInput.files[0]);
            if (photoInput && photoInput.files[0]) {
                formData.append('photo', photoInput.files[0]);
            }
            
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Uploading & Analyzing...';
            btn.disabled = true;
            const token = localStorage.getItem('token');
            try {
                const res = await fetch('/api/candidate/upload_resume', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` },
                    body: formData
                });
                const data = await res.json();
                if (res.ok) {
                    document.getElementById('resume-analysis').style.display = 'block';
                    document.getElementById('ats-score').innerText = data.analysis.ATS_Compatibility_Score || data.analysis["ATS Compatibility Score"] || 'N/A';
                    document.getElementById('skills-list').innerText = data.analysis.Skills.join(', ');
                    document.getElementById('strengths-list').innerText = data.analysis.Strengths.join(', ');
                } else {
                    alert("Upload failed: " + data.message);
                }
            } catch(e) {
                alert("Error during upload.");
            } finally {
                btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up"></i> Upload & Analyze';
                btn.disabled = false;
            }
        });
    }
}

async function startInterview() {
    try {
        const res = await fetch('/api/interview/start', {
            method: 'POST',
            headers: getAuthHeaders()
        });
        const data = await res.json();
        if (res.ok) {
            window.location.href = `/interview/${data.interview_id}`;
        } else {
            alert(data.message);
        }
    } catch(e) {
        alert("Error starting interview");
    }
}

async function loadAdminData() {
    try {
        const res1 = await fetch('/api/admin/system-health', { headers: getAuthHeaders() });
        if(res1.ok) {
            const health = await res1.json();
            document.getElementById('admin-status').innerText = health.status;
            document.getElementById('admin-uptime').innerText = health.uptime;
        }

        const res2 = await fetch('/api/admin/users', { headers: getAuthHeaders() });
        if(res2.ok) {
            const users = await res2.json();
            const tbody = document.getElementById('admin-users');
            tbody.innerHTML = '';
            users.forEach(u => {
                tbody.innerHTML += `
                    <tr>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${u.id}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${u.name}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${u.email}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${u.role}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0; text-align:right;">
                            <button class="btn" style="background:#dc2626; color:white; padding: 0.3rem 0.6rem; font-size:0.9rem;" onclick="deleteUser(${u.id})"><i class="fa-solid fa-trash"></i> Remove</button>
                        </td>
                    </tr>
                `;
            });
        } else {
            window.location.href = '/login';
            return;
        }
    } catch(e) { console.error(e); }
}

async function deleteUser(userId) {
    if(!confirm("Are you sure you want to completely remove this user and all their associated data? This action cannot be undone.")) return;
    
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/admin/user/${userId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if(res.ok) {
            alert("User successfully removed.");
            loadAdminData(); // refresh table
        } else {
            alert("Failed to remove user: " + data.message);
        }
    } catch(e) {
        console.error(e);
        alert("An error occurred while removing the user.");
    }
}

async function loadHRData() {
    try {
        const res = await fetch('/api/hr/dashboard-stats', { headers: getAuthHeaders() });
        if(res.ok) {
            const data = await res.json();
            document.getElementById('hr-total').innerText = data.total_interviews;
            document.getElementById('hr-pending').innerText = data.pending_interviews;
            document.getElementById('hr-avg').innerText = data.avg_score.toFixed(1);
        } else {
            window.location.href = '/login';
            return;
        }
        
        const res2 = await fetch('/api/hr/interviews', { headers: getAuthHeaders() });
        if(res2.ok) {
            const interviews = await res2.json();
            const tbody = document.getElementById('hr-candidates-list');
            if (interviews.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="padding:10px;">No candidates found.</td></tr>';
            } else {
                tbody.innerHTML = interviews.map(i => {
                    const statusHtml = i.status === 'completed' 
                        ? '<span style="background-color: rgba(34, 197, 94, 0.2); color: #16a34a; padding: 0.3rem 0.8rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;"><i class="fa-solid fa-check-circle"></i> Attended</span>'
                        : '<span style="background-color: rgba(239, 68, 68, 0.2); color: #dc2626; padding: 0.3rem 0.8rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;"><i class="fa-solid fa-times-circle"></i> Not Attended</span>';
                    return `
                    <tr>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${i.candidate_name}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">#${i.interview_id}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${statusHtml}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;">${i.overall_rating || 'N/A'}</td>
                        <td style="padding:10px; border-bottom:1px solid #e2e8f0;"><button class="btn btn-outline" style="padding: 0.3rem 0.6rem;" onclick="viewCandidate(${i.candidate_id}, ${i.interview_id})">View</button></td>
                    </tr>
                    `;
                }).join('');
            }
        }
    } catch(e) { console.error(e); }
}

async function viewCandidate(candId, intId) {
    try {
        const token = localStorage.getItem('token');
        const res = await fetch(`/api/hr/candidate/${candId}/interview/${intId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        
        document.getElementById('modal-name').innerText = data.candidate.name;
        document.getElementById('modal-skills').innerText = data.candidate.skills || 'N/A';
        document.getElementById('modal-education').innerText = data.candidate.education || 'N/A';
        
        const resumeBtn = document.getElementById('modal-resume-btn');
        const noResume = document.getElementById('modal-no-resume');
        if (data.candidate.resume_url) {
            resumeBtn.href = data.candidate.resume_url;
            resumeBtn.style.display = 'inline-block';
            noResume.style.display = 'none';
        } else {
            resumeBtn.style.display = 'none';
            noResume.style.display = 'block';
        }
        
        const photoEl = document.getElementById('modal-photo');
        const noPhoto = document.getElementById('modal-no-photo');
        if (data.candidate.photo_url) {
            photoEl.src = data.candidate.photo_url;
            photoEl.style.display = 'block';
            noPhoto.style.display = 'none';
        } else {
            photoEl.src = "";
            photoEl.style.display = 'none';
            noPhoto.style.display = 'block';
        }
        
        document.getElementById('candidate-modal').style.display = 'flex';
    } catch(e) {
        console.error(e);
        alert("Error loading candidate details.");
    }
}

function closeModal() {
    document.getElementById('candidate-modal').style.display = 'none';
}

function togglePassword(inputId, iconId) {
    const pwdInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    if (pwdInput.type === "password") {
        pwdInput.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
    } else {
        pwdInput.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
    }
}

// Forgot Password Form Submit
document.addEventListener('DOMContentLoaded', () => {
    const forgotForm = document.getElementById('forgot-password-form');
    if (forgotForm) {
        forgotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('reset-email').value;
            const msgEl = document.getElementById('forgot-message');
            
            msgEl.style.color = "var(--gray)";
            msgEl.innerText = "Sending...";
            
            try {
                const res = await fetch('/api/auth/forgot-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const data = await res.json();
                
                if (res.ok) {
                    msgEl.style.color = "var(--primary)";
                    msgEl.innerText = data.message;
                    if (data.reset_link) {
                        const demoLinkContainer = document.getElementById('demo-link-container');
                        const demoLink = document.getElementById('demo-reset-link');
                        demoLink.href = data.reset_link;
                        demoLinkContainer.style.display = 'block';
                    }
                } else {
                    msgEl.style.color = "#ef4444";
                    msgEl.innerText = data.message || "An error occurred.";
                }
            } catch (err) {
                console.error(err);
                msgEl.style.color = "#ef4444";
                msgEl.innerText = "Network error. Try again later.";
            }
        });
    }

    // Reset Password Form Submit
    const resetForm = document.getElementById('reset-password-form');
    if (resetForm) {
        resetForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            const msgEl = document.getElementById('reset-message');
            
            if (newPassword !== confirmPassword) {
                msgEl.style.color = "#ef4444";
                msgEl.innerText = "Passwords do not match.";
                return;
            }
            
            // Extract token from URL
            const urlParams = new URLSearchParams(window.location.search);
            const token = urlParams.get('token');
            
            if (!token) {
                msgEl.style.color = "#ef4444";
                msgEl.innerText = "Invalid or missing token.";
                return;
            }
            
            msgEl.style.color = "var(--gray)";
            msgEl.innerText = "Resetting password...";
            
            try {
                const res = await fetch('/api/auth/reset-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token, new_password: newPassword })
                });
                const data = await res.json();
                
                if (res.ok) {
                    msgEl.style.color = "var(--primary)";
                    msgEl.innerText = data.message;
                    document.getElementById('login-link-container').style.display = 'block';
                    resetForm.reset();
                } else {
                    msgEl.style.color = "#ef4444";
                    msgEl.innerText = data.message || "An error occurred.";
                }
            } catch (err) {
                console.error(err);
                msgEl.style.color = "#ef4444";
                msgEl.innerText = "Network error. Try again later.";
            }
        });
    }
});
