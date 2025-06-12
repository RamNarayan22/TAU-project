from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from Student.models import Ticket, Department, SLAConfig, SLABreachLog, PRIORITY_CHOICES

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_superuser)
def global_sla_dashboard(request):
    # Get date range (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Overall metrics
    total_tickets = Ticket.objects.filter(created_at__gte=start_date).count()
    resolved_tickets = Ticket.objects.filter(
        created_at__gte=start_date,
        status='resolved'
    ).count()
    
    resolution_rate = (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0
    
    # Average resolution time
    avg_resolution_time = Ticket.objects.filter(
        created_at__gte=start_date,
        resolved_at__isnull=False
    ).annotate(
        resolution_time=ExpressionWrapper(
            F('resolved_at') - F('created_at'),
            output_field=fields.DurationField()
        )
    ).aggregate(
        avg_time=Avg('resolution_time')
    )['avg_time']
    
    avg_resolution_hours = avg_resolution_time.total_seconds() / 3600 if avg_resolution_time else 0
    
    # SLA breaches
    total_breaches = SLABreachLog.objects.filter(
        breached_at__gte=start_date
    ).count()
    
    sla_breach_rate = (total_breaches / total_tickets * 100) if total_tickets > 0 else 0
    
    # Department-wise metrics
    departments = Department.objects.all()
    department_metrics = []
    
    for dept in departments:
        dept_tickets = Ticket.objects.filter(
            department=dept,
            created_at__gte=start_date
        )
        
        dept_total = dept_tickets.count()
        if dept_total > 0:
            dept_resolved = dept_tickets.filter(status='resolved').count()
            dept_breaches = SLABreachLog.objects.filter(
                ticket__department=dept,
                breached_at__gte=start_date
            ).count()
            
            department_metrics.append({
                'name': dept.name,
                'total_tickets': dept_total,
                'resolution_rate': (dept_resolved / dept_total * 100),
                'breach_rate': (dept_breaches / dept_total * 100)
            })
    
    # Priority-wise metrics
    priority_metrics = []
    for priority, _ in PRIORITY_CHOICES:
        priority_tickets = Ticket.objects.filter(
            priority=priority,
            created_at__gte=start_date
        )
        
        priority_total = priority_tickets.count()
        if priority_total > 0:
            priority_resolved = priority_tickets.filter(status='resolved').count()
            priority_breaches = SLABreachLog.objects.filter(
                ticket__priority=priority,
                breached_at__gte=start_date
            ).count()
            
            priority_metrics.append({
                'priority': priority,
                'total_tickets': priority_total,
                'resolution_rate': (priority_resolved / priority_total * 100),
                'breach_rate': (priority_breaches / priority_total * 100)
            })
    
    context = {
        'total_tickets': total_tickets,
        'resolution_rate': resolution_rate,
        'avg_resolution_hours': avg_resolution_hours,
        'sla_breach_rate': sla_breach_rate,
        'department_metrics': department_metrics,
        'priority_metrics': priority_metrics,
        'days': days,
        'priority_choices': PRIORITY_CHOICES
    }
    
    return render(request, 'core/global_sla_dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def global_sla_config(request):
    departments = Department.objects.all()
    department_configs = []
    
    for dept in departments:
        configs = SLAConfig.objects.filter(department=dept)
        department_configs.append({
            'department': dept,
            'configs': configs
        })
    
    context = {
        'department_configs': department_configs,
        'priority_choices': PRIORITY_CHOICES
    }
    
    return render(request, 'core/global_sla_config.html', context)

@login_required
@user_passes_test(is_superuser)
def global_sla_report(request):
    # Get date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get all breaches
    breaches = SLABreachLog.objects.filter(
        breached_at__gte=start_date
    ).order_by('-breached_at')
    
    # Department filter
    department_id = request.GET.get('department')
    if department_id:
        breaches = breaches.filter(ticket__department_id=department_id)
    
    # Priority filter
    priority = request.GET.get('priority')
    if priority:
        breaches = breaches.filter(ticket__priority=priority)
    
    context = {
        'breaches': breaches,
        'days': days,
        'departments': Department.objects.all(),
        'priority_choices': PRIORITY_CHOICES,
        'selected_department': department_id,
        'selected_priority': priority
    }
    
    return render(request, 'core/global_sla_report.html', context)
