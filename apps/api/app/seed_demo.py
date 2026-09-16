import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import init_db

from app.models.user import User, RoleEnum
from app.models.facility import Facility, Room, Tank
from app.models.project import Project
from app.models.census_event import CensusEvent
from app.models.water_quality_log import WaterQualityLog
from app.models.incident_report import IncidentReport
from app.models.audit_log import AuditLog


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


async def seed_facility_demo_data():
    """Populates realistic demo data for University of Windsor ACARE facility presentation."""
    print("--- Initializing ACARE Demo Facility Database Seeding ---")
    await init_db()

    # 1. Facility Setup
    fac = await Facility.find_one({"name": "University of Windsor Central Aquatic Facility"})
    if not fac:
        fac = Facility(
            name="University of Windsor Central Aquatic Facility",
            code="UWIN-CAF",
            address="Sunset Ave, Windsor, ON N9B 3P4",
            active=True,
        )
        await fac.insert()
        print(f"  [+] Created Facility: {fac.name}")

    # 2. Rooms Setup
    room_101 = await Room.find_one({"room_number": "101", "facility_id": str(fac.id)})
    if not room_101:
        room_101 = Room(facility_id=str(fac.id), room_number="101", name="Zebrafish Suite A", active=True)
        await room_101.insert()

    room_102 = await Room.find_one({"room_number": "102", "facility_id": str(fac.id)})
    if not room_102:
        room_102 = Room(facility_id=str(fac.id), room_number="102", name="Medaka & Xenopus Suite B", active=True)
        await room_102.insert()
    print("  [+] Created Rooms 101 & 102")

    # 3. Tanks 1–14 Setup
    tanks = []
    for t_num in range(1, 15):
        rm_id = str(room_101.id) if t_num <= 8 else str(room_102.id)
        t_str = f"Tank {t_num}"
        existing_tank = await Tank.find_one({"tank_number": t_str, "room_id": rm_id})
        if not existing_tank:
            tank_obj = Tank(
                room_id=rm_id,
                tank_number=t_str,
                capacity=50,
                status="active",
                is_quarantined=False,
            )
            await tank_obj.insert()
            tanks.append(tank_obj)
        else:
            tanks.append(existing_tank)
    print(f"  [+] Seeded {len(tanks)} Tanks (Tanks 1-14)")


    # 4. Users Setup (Admin, Chair, Manager, Staff)
    hashed_pw = pwd_context.hash("ChangeMe123!")

    async def get_or_create_user(email, first, last, role):
        u = await User.find_one({"email": email})
        if not u:
            u = User(
                first_name=first,
                last_name=last,
                email=email,
                password_hash=hashed_pw,
                role=role,
                requested_role=role,
                approved=True,
                assigned_tank_ids=[str(t.id) for t in tanks],
            )

            await u.insert()
        return u

    admin_user = await get_or_create_user("superadmin@uwindsor.ca", "Super", "Admin", RoleEnum.admin)
    chair_user = await get_or_create_user("chair@uwindsor.ca", "Dr. Windsor", "Chair", RoleEnum.chair)
    mgr_user = await get_or_create_user("manager@uwindsor.ca", "Facility", "Manager", RoleEnum.manager)
    staff_user = await get_or_create_user("tech@uwindsor.ca", "Staff", "Technician", RoleEnum.staff)
    print("  [+] Created Demo Users (Admin, Chair, Manager, Staff)")

    # 5. AUPP Projects
    proj_1 = await Project.find_one({"aupp_number": "AUPP-2026-001"})
    if not proj_1:
        proj_1 = Project(
            title="Zebrafish Cardiac Regeneration Model",
            aupp_number="AUPP-2026-001",
            pi_id=str(chair_user.id),
            pi_name="Dr. Windsor",
            status="active",
            start_date=datetime.now(timezone.utc) - timedelta(days=60),
            end_date=datetime.now(timezone.utc) + timedelta(days=300),
            created_by=str(mgr_user.id),
        )
        await proj_1.insert()

    proj_2 = await Project.find_one({"aupp_number": "AUPP-2026-002"})
    if not proj_2:
        proj_2 = Project(
            title="Medaka Neural Development Analysis",
            aupp_number="AUPP-2026-002",
            pi_id=str(chair_user.id),
            pi_name="Dr. Windsor",
            status="active",
            start_date=datetime.now(timezone.utc) - timedelta(days=45),
            end_date=datetime.now(timezone.utc) + timedelta(days=315),
            created_by=str(mgr_user.id),
        )
        await proj_2.insert()
    print("  [+] Seeded Active AUPP Projects (AUPP-2026-001, AUPP-2026-002)")

    # 6. Historical Data (Last 30 Days)
    today = datetime.now(timezone.utc)
    for day_offset in range(30, 0, -1):
        log_date = (today - timedelta(days=day_offset)).date()
        date_str = log_date.strftime("%Y-%m-%d")

        # Water Quality Log
        for t in tanks[:6]:
            wq_key = f"demo-wq-{t.id}-{date_str}"
            if not await WaterQualityLog.find_one({"idempotency_key": wq_key}):
                wq = WaterQualityLog(
                    idempotency_key=wq_key,
                    tank_id=str(t.id),
                    project_id=str(proj_1.id),
                    type="daily",
                    date=log_date,
                    parameters={
                        "ph": round(7.2 + (day_offset % 3) * 0.1, 2),
                        "temperature": round(26.0 + (day_offset % 2) * 0.5, 1),
                        "dissolved_oxygen": round(7.5 - (day_offset % 4) * 0.2, 1),
                    },
                    comments="Normal daily round check.",
                    created_by=str(staff_user.id),
                )
                await wq.insert()

    # 7. Demo Incident Report (with Vet Contacted flag)
    inc_key = "demo-inc-001"
    if not await IncidentReport.find_one({"idempotency_key": inc_key}):
        inc = IncidentReport(
            idempotency_key=inc_key,
            project_id=str(proj_1.id),
            tank_id=str(tanks[3].id),
            date=today.date(),
            time="11:15",
            problem="Nitrite surge detected in biofilter loop. 2 fish showing signs of distress.",
            comments="Veterinarian Dr. Smith notified immediately.",
            treatment="Executed 30% system water change and adjusted bio-ring flow rate.",
            aquatic_condition_checked=True,
            vet_contacted=True,
            researcher_notified=True,
            created_by=str(staff_user.id),
        )
        await inc.insert()
        print("  [+] Seeded Aquatic Incident Report with Vet Contacted Flag")

    print("[SUCCESS] ACARE Facility Demo Data Seeding Complete!")



if __name__ == "__main__":
    asyncio.run(seed_facility_demo_data())
